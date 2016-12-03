var modules = angular.module('gransk.modules');


modules.controller('EntitiesCtrl', ['$scope', '$cookies', '$location', 'entity', 'config', 'hotkeys', function($scope, $cookies, $location, entity, config, hotkeys) {
  $scope.$parent.mode = 'entities';
  $scope.index = $cookies.get('entindex') ? $cookies.get('entindex') * 1 : 0;
  $scope.lock_msg = false;
  $scope.entity_facets = {
    type: {}
  };
  $scope.entities = {
    hits: []
  };

  $scope.show = $cookies.get('es') ? $cookies.get('es') : 'documents';

  $scope.set_show = function(show) {
    $scope.show = show;
    $cookies.put('es', show);
  };

  hotkeys.clear();
  hotkeys.listen(function(action) {
    var result = hotkeys.get(action, $scope.entities.hits.length, $scope.entities.pages, $scope.entities.page, $scope.index);

    if (result.page >= 0) $scope.change_entity_page(result.page, result.index);
    if (result.index >= 0) $scope.set_entity(result.index);

    $scope.$apply();
  });

  $scope.$on('reset_search', function() {
    $scope.entity_facets = {
      type: {}
    };
  });

  $scope.$on('entities', function(e, entities) {
    $scope.entities = entities;
    entity.set_by_index(0);
    $scope.entity = entity.get_by_index(0);
    $scope.set_entity(0);
  });

  $scope.set_entity = function(index) {
    $scope.index = index;
    entity.set_by_index(index);
    $cookies.put('entindex', index);
    $scope.entity = entity.get_by_index(index);
  };

  if ($location.search().lock) {
    var q = 'entity_id:' + $location.search().lock;
    if ($location.search().q) {
      q += ' AND ' +  $location.search().q;
    }
    $scope.$parent.submit_query(q);
    $scope.lock_msg = true;
    $scope.set_entity(0);
  } else {
    $scope.$parent.submit_query($scope.$parent.query_string);
    $scope.set_entity(0);
  }

  $scope.change_entity_page = function(page, _index) {
    $scope.index = _index ? _index : 0;
    entity.search($scope.query_string, page, $scope.entity_facets, function(entites) {
      $scope.entities = entites;
      $scope.entity = entity.get_by_index($scope.index);
      entity.set_by_index(0);
      $scope.entity = entity.get_by_index(0);
    });
  };

  $scope.get_documents = function(page) {
    entity.get_documents($scope.entity, page);
  };

  $scope.$watch('entity_facets', function() {
    if ($location.search().lock) return;
    $cookies.putObject('ef', $scope.entity_facets);
    entity.search($scope.query_string, 0, $scope.entity_facets, function(entites) {
      $scope.entities = entites;
      $scope.entity = entity.get_by_index($scope.index);
      entity.set_by_index(0);
      $scope.entity = entity.get_by_index(0);
    });
  }, true);
}]);

modules.service('entity', function($cookies, config, client, aggs, query, pagecount, related) {
  var entities;

  return {
    search: function(query_string, page, facets, callback) {
      page = Math.max(page, 0);

      if (entities) {
        page = Math.min(page, entities.pages);
      }

      var obj = query.generate('entity', 'value', query_string, [], page, facets, config.pagesize);

      try {
        client.search(obj).then(function(resp) {
          entities = resp.hits;
          entities.pages = pagecount.compute(entities.total);
          entities.page = page;
          entities.facets = {
            entity_type: {}
          };

          resp.aggregations.type.buckets.map(function(bucket) {
            entities.facets.entity_type[bucket.key] = bucket.doc_count;
          });

          callback(entities);
        });
      }
      catch (e) {
        callback({hits:[]});
      }
    },

    set_entities: function(_entities) {
      entities = _entities;
    },

    set_by_index: function(index) {
      if (!entities) return;
      var entity = entities.hits[index];
      if (!entity) return;

      this.get_documents(entity, 0);
      this.load_related(entity);

      return entity;
    },

    get_by_index: function(index) {
      if (!entities) return;
      return entities.hits[index];
    },

    load_related: function(entity) {
      related.load('entity', entity._source.entity_id, function(related) {
        entity.related = related;
      });
    },

    get_documents: function(entity, page) {
      entity.docpage = page;
      entity.docpage = Math.max(0, entity.docpage);
      if (entity.docpages >= 0) {
        entity.docpage = Math.min(entity.docpages, entity.docpage);
      }

      $cookies.put('edp', entity.docpage);

      client.search({
        index: 'gransk',
        type: 'in_doc',
        body: {
          size: config.pagesize,
          from: config.pagesize * entity.docpage,
          query: {
            match: {
              entity_id: entity._source.entity_id
            }
          }
        }
      }).then(function(resp) {
        entity.documents = resp.hits;
        entity.docpages = pagecount.compute(entity.documents.total);
      });
    }
  };
});



modules.directive('entitynetwork', function($http) {
  var colors = "#369EAD #7F6084 #86B402 #A2D1CF #C8B631 #6DBCEB #52514E #4F81BC #A064A1 #F79647".split(' ');
  var graph = Viva.Graph.graph();
  var graphics = Viva.Graph.View.svgGraphics();
  var nodeSize = 10;
  var renderer;
  var color_cache = {};
  var layout = Viva.Graph.Layout.forceDirected(graph, {
    springLength : 30,
    springCoeff : 0.0008,
    dragCoeff : 0.009,
    gravity : -1.2,
    thetaCoeff: 0.8
});


  return {
    restrict: 'E',
    template: '<div>' +
      '  <div id="graph-controls">' +
      '    <input type="radio" ng-model="hops" value="1" id="hop-1" /> <label for="hop-1">1 hop</label>&nbsp;' +
      '    <input type="radio" ng-model="hops" value="2" id="hop-2" /> <label for="hop-2">2 hops</label>&nbsp;' +
      '    <input type="radio" ng-model="hops" value="3" id="hop-3" /> <label for="hop-3">3 hops</label>&nbsp;' +
      '    <a href ng-show="running" ng-click="stop()">Stop</a>' +
      '    <a href ng-hide="running" ng-click="start()">Start</a>' +
      '  </div>' +
      '  <div id="graph" ng-class="{\'active\':running}"></div>' +
      '</div>',
    scope: {
      entity: '='
    },
    link: function(scope, element) {
      scope.hops = '1';
      var timeout;

      scope.running = false;

      scope.stop = function() {
        renderer.pause();
        scope.running = false;
      }

      scope.start = function() {
        renderer.resume();
        scope.running = true;
      }

      graphics.node(
        function(node) {
          if (!(node.data.type in color_cache)) {
            color_cache[node.data.type] = colors[Object.keys(color_cache).length];
          }

          var fill = node.data.entity_id === scope.entity._source.entity_id ? '#ff0000' : color_cache[node.data.type];
          var ui = Viva.Graph.svg('g');
          var svgText = Viva.Graph.svg('text').attr('y', '-4px').text(node.data.value).attr('font-size', 9);
          var img = Viva.Graph.svg('circle').attr('r', nodeSize / 2).attr('fill', fill).attr('cx', nodeSize / 2).attr('cy', nodeSize / 2);
          ui.append(svgText);
          ui.append(img);

          return ui;
        }).placeNode(
        function(nodeUI, pos) {
          nodeUI.childNodes[0].attr('x', (nodeUI.childNodes[0].getBBox().width / 2) * -1 + nodeSize / 2);
          nodeUI.attr('transform', 'translate(' + (pos.x - nodeSize / 2) +
            ',' + (pos.y - nodeSize / 2) + ')');
        });

      var seed = null;

      scope.$watchCollection('[entity, hops]', function() {
        graph.clear();

        try {
          renderer.dispose();
        } catch (e) {}

        renderer = Viva.Graph.View.renderer(graph, {
          container: angular.element(element.children()[0]).children()[1],
          graphics: graphics,
          layout : layout
        });

        if (!scope.entity) return;


        seed = scope.entity._source.entity_id;
        $http.get('/network?hops=' + scope.hops + '&entity_id=' + scope.entity._source.entity_id).then(function(network) {
          if (network.data.seed && network.data.seed.toLowerCase() !== seed.toLowerCase()) return;

          scope.network = network;
          graph.clear();

          for (var node in network.data.nodes) {
            network.data.nodes[node].entity_id = node;
            graph.addNode(node, network.data.nodes[node]);
          }

          network.data.links.map(function(link) {
            graph.addLink(link[0], link[1], link[2]);
          });

          renderer.run();
          scope.running = true;
        });
      }, true);
    }
  };
});
