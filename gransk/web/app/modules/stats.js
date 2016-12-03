var modules = angular.module('gransk.modules');

modules.controller('StatisticsCtrl', ['$scope', function($scope) {
  $scope.$parent.mode = 'statistics';
  $scope.$parent.submit_query($scope.$parent.query_string);
}]);

modules.service('stats', function(config, client, aggs) {
  var statistics = {
    aggs: {},
    counts: {}
  };

  return {
    load: function(callback) {
      var _aggs = JSON.parse(JSON.stringify(aggs.get(true)));
      _aggs.entities = {
        cardinality: {
          field: "raw_entity"
        }
      };
      _aggs.documents = {
        cardinality: {
          field: "id"
        }
      };

      _aggs.added_histogram = {
        nested : {
            path : 'meta'
        },
        aggs: {
          by_hour: {
            date_histogram: {
              field: 'meta.added',
              interval: '10s',
              format: 'epoch_second'
            }
          }
        }
      }

      client.search({
        index: 'gransk',
        body: {
          size: 0,
          query: {
            match_all: {}
          },
          aggs: _aggs
        }
      }).then(function(resp) {
        statistics.counts = {
          entities: resp.aggregations.entities.value,
          documents: resp.aggregations.documents.value
        };

        delete resp.aggregations.entities;
        delete resp.aggregations.documents;

        resp.aggregations.raw_entity.buckets.map(function(entity, i) {
          resp.aggregations.raw_entity.buckets[i].key = JSON.parse(resp.aggregations.raw_entity.buckets[i].key);
        });

        statistics.histogram = resp.aggregations.added_histogram;
        delete resp.aggregations.added_histogram;
        statistics.aggs = resp.aggregations;

        callback(statistics);
      });
    }
  };
});

modules.directive('histogram', function() {
  return {
    transclude: true,
    restrict: "E",
    template: '<div class="histogram-container"><div class="histogram-header">Added documents</div><div class="histogram">{{histogram}}</div></div>',
    scope: {
      histogram: '='
    },
    link: function(scope, element) {
      scope.$watch('histogram', function() {
        if (!scope.histogram) return;
        var margin = {top: 10, right: 30, bottom: 30, left: 50},
		    width = document.getElementById('mainstats').offsetWidth - margin.left - margin.right - 30,
		    height = 200 - margin.top - margin.bottom;

  		var parseDate = d3.time.format("%m/%d/%Y %I:%M:%S %p").parse;
  		var formatDate = d3.time.format("%d/%m %H:%M");
  		var formatCount = d3.format(",.0f");

  		var x = d3.time.scale().range([0, width]);
  		var y = d3.scale.linear().range([height, 0]);

  		var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(6).tickFormat(formatDate);
  		var yAxis = d3.svg.axis().scale(y).orient("left").ticks(6);

  		// Create the SVG drawing area
      angular.element(element.children()[0]).children()[1].innerHTML = '';
  		var svg = d3.select(angular.element(element.children()[0]).children()[1])
  		  .append("svg")
  		  .attr("width", width + margin.left + margin.right)
  		  .attr("height", height + margin.top + margin.bottom)
        //.attr('fill', '#FEFFFE')
        .attr('fill', '#888')
  		  .append("g")
  		  .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  		// Get the data

      var data = [];

      scope.histogram.by_hour.buckets.map(function(bucket) {
        for (var i=0; i<bucket.doc_count; i++) {
          data.push({
            created_date: new Date(bucket.key*1000)
          });
        }
      })

  		  // Determine the first and list dates in the data set
  		  var monthExtent = d3.extent(data, function(d) { return d.created_date; });

  		  // Create one bin per month, use an offset to include the first and last months
  		  var monthBins = d3.time.hours(d3.time.hour.offset(new Date(monthExtent[0].getTime() - 60 * 60 * 12 * 1000),-1),
  		                                 d3.time.hour.offset(new Date(new Date().getTime() + 60 * 60 * 12 * 1000),1));

  		  // Use the histogram layout to create a function that will bin the data
  		  var binByMonth = d3.layout.histogram()
  		    .value(function(d) { return d.created_date; })
  		    .bins(monthBins);

  		  // Bin the data by month
  		  var histData = binByMonth(data);

  		  // Scale the range of the data by setting the domain
  		  x.domain(d3.extent(monthBins));
  		  y.domain([0, d3.max(histData, function(d) { return d.y; })]);

  		  svg.selectAll(".bar")
  		      .data(histData)
  		    .enter().append("rect")
  		      .attr("class", "bar")
  		      .attr("x", function(d) { return x(d.x); })
  		      .attr("width", function(d) { return x(new Date(d.x.getTime() + d.dx))-x(d.x)-1; })
  		      .attr("y", function(d) { return y(d.y); })
  		      .attr("height", function(d) { return height - y(d.y); });

  		  // Add the X Axis
  		  svg.append("g")
  		      .attr("class", "x axis")
  		      .attr("transform", "translate(0," + height + ")")
  		      .call(xAxis);

  		  // Add the Y Axis and label
  		  svg.append("g")
  		     .attr("class", "y axis")
  		     .call(yAxis)
  		    .append("text")
  		      .attr("transform", "rotate(-90)")
  		      .attr("y", 6)
  		      .attr("dy", ".71em")
  		      .style("text-anchor", "end");

  		});
    }
  }
});

modules.directive('pie', function($timeout) {
  var colors = "#369EAD #C24642 #7F6084 #86B402 #A2D1CF #C8B631 #6DBCEB #52514E #4F81BC #A064A1 #F79647".split(' ');
  var width = window.innerWidth;

  return {
    transclude: true,
    restrict: "E",
    template: '<div class="pie-container"><div class="pie-header">{{pid}}</div><div class="pie"></div></div>',
    scope: {
      pid: '=',
      data: '='
    },
    link: function(scope, element) {
      var pie = new d3pie(angular.element(angular.element(element[0]).children()[0]).children()[1], {
        header: {
         title: {text: null}
       },
        size: {
          canvasHeight: 200,
          canvasWidth: 270,
          pieOuterRadius: "88%"
        },
        data: {
          content: []
        },
        labels: {
          outer: {
            pieDistance: 25
          },
          inner: {
            format: "value"
          },
          mainLabel: {
            font: "verdana",
            fontSize: 13
          },
          percentage: {
            color: "#e1e1e1",
            font: "verdana",
            decimalPlaces: 0
          },
          value: {
            color: "#e1e1e1",
            font: "verdana",
            fontSize: 13
          },
          lines: {
            enabled: true,
            color: "#cccccc"
          },
          truncation: {
            enabled: true
          }
        },
        effects: {
          pullOutSegmentOnClick: {
            effect: "linear",
            speed: 100,
            size: 8
          },
          load: {
        		effect: "none"
        	}
        }
      });

      scope.$watch('data', function() {
        scope.content = [];

        scope.data.buckets.map(function(bucket, i) {
          scope.content.push({
            label: bucket.key,
            value: bucket.doc_count,
            color: colors[i % colors.length]
          });
        });

        pie.updateProp("data.content", scope.content);
      });
    }
  };
});
