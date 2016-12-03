var modules = angular.module('gransk.modules', []);
var app = angular.module('gransk', ['ngRoute', 'ngCookies', 'ngStorage', 'gransk.modules']);

var ESHOST;

app.constant('config', {
  eshost: ESHOST, // This variable is fetched from config.yml through Flask templating.
  app_title: 'Gransk',
  pagesize: 6,
  number_of_fragments: 15,
  fragment_size: 150,
  aggregation_size: 4,
  aggregation_fields: ['type', 'ext', 'status', 'doctype', 'raw_entity', 'tag']
});

app.filter('to_trusted', ['$sce', function($sce) {
  var map = {
    '[[': '<',
    ']]': '>'
  };
  return function(text) {
    if (!text) return '';
    text = text.replace(new RegExp('<[^>]+>', 'g'), '');
    text = text.replace(/(\[\[|\]\])/g, function(hit) {
      return map[hit];
    });
    return $sce.trustAsHtml(text);
  };
}]);

app.config(function($routeProvider) {
  $routeProvider
    .when('/statistics', {
      templateUrl: '/static/views/statistics.html',
      controller: 'StatisticsCtrl'
    })
    .when('/documents', {
      templateUrl: '/static/views/documents.html',
      reloadOnSearch: true,
      controller: 'DocumentsCtrl'
    })
    .when('/entities', {
      templateUrl: '/static/views/entities.html',
      reloadOnSearch: true,
      controller: 'EntitiesCtrl'
    })
    .when('/live', {
      templateUrl: '/static/views/live.html',
      reloadOnSearch: true,
      controller: 'LiveCtrl'
    })
    .when('/latest', {
      templateUrl: '/static/views/latest.html',
      reloadOnSearch: true,
      controller: 'LatestCtrl'
    })
    .when('/story', {
      templateUrl: '/static/views/story.html',
      reloadOnSearch: true,
      controller: 'StoryCtrl'
    })
    .otherwise({
      redirectTo: '/statistics'
    });
});

app.controller('MainCtrl', function($scope, $cookies, $location, config, doc, stats, entity, $http, client, format) {
  $scope.query_string = $cookies.get('q');

  if (!$scope.query_string) {
    $scope.query_string = '';
  }

  $scope.mode = null;

  $scope.counts = {
    entities: 0,
    documents: 0
  };

  $scope.prettify = function(key, value) {
    return format.auto(key, value);
  };

  $scope.is_int =function(value) {
    return !isNaN(value*1);
  }

  $scope.$on('$locationChangeSuccess', function(event){
    $scope.lock = $location.search().lock;
  })

  $scope.set_title = function(subtitle, extra) {
    $scope.title = config.app_title + ' | ' + subtitle;
    if (extra) {
      $scope.title += ' | ' + extra;
    }
  };

  $scope.set_title_number = function(subtitle, number) {
    if (number === 0) {
      $scope.title = config.app_title + ' | ' + subtitle;
    }
    else {
      $scope.title = '(' + number + ') ' + config.app_title + ' | ' + subtitle;
    }
  }

  $scope.$watch('mode', function() {
    if (!$scope.mode) return;
    var mode = $scope.mode.charAt(0).toUpperCase() + $scope.mode.slice(1);
    $scope.set_title(mode);
  });

  $scope.form_submit_query = function(query) {
    $location.search('lock', null);
    $scope.$broadcast('reset_search');
    $scope.submit_query(query);
    $cookies.put('q', query);
    if (query.length > 0 && $scope.mode === 'statistics') {
      $location.path('/documents');
    }
  };

  $scope.submit_query = function(query) {
    $scope.document_page = 0;
    $cookies.put('dp', $scope.document_page);
    $scope.query(query);
  };

  $scope.query = function(query) {
    doc.search(query, 0, $scope.document_facets, function(docs) {
      $scope.counts.documents = docs.total;
      $scope.$broadcast('docs', docs);
    });

    entity.search(query, 0, $scope.entity_facets, function(entities) {
      $scope.counts.entities = entities.total;
      $scope.$broadcast('entities', entities);
    });
  };

  $scope.highlight = function(what, label) {
    return label.replace(new RegExp(what, 'g'), '[[span]]' + what + '[[/span]]');
  };

  $scope.clear_data = function() {
    if (confirm('This will remove processed data.')) {
      $http.delete('/data').then(function() {
        location.reload();
      });
    }
  };

  $scope.json_stringify = function(obj) {
    return JSON.stringify(obj, null, 2);
  }

  stats.load(function(statistics) {
    $scope.statistics = statistics;
  });
});

app.directive('navhint', function() {
  return {
    restrict: 'E',
    template: '<div id="nav-hint"><em>Hint:</em> Use \'<\', \'z\', \'p\' and \'n\' to navigate results.</div',
    link: function(scope) {}
  };
});

app.directive('dropzone', function($timeout) {
  return {
    restrict: 'E',
    template: '<div id="upload-container">' +
      '<div id="previews"></div>' +
      '<div id="upload-progress">' +
      '<div id="upload-inner" class="inner"></div>' +
      '</div>' +
      '</div>',
    scope: {},
    compile: function() {
      return {
        post: function(scope, element) {
          var elements = angular.element(element.children()[0]).children();
          scope.progress_bar = elements[1];
          var elem = angular.element(elements[1]).children()[0];

          window.onbeforeunload = null;

          var show_progress = function(show) {
            scope.progress_bar.style.display = show ? 'block' : 'none';
          };

          show_progress(false);

          scope.added = 0;
          scope.completed = 0;
          scope.progress = 0;

          var added_timeout;

          scope.get_width = function(exact) {
            if (scope.added === 0) return 0;
            scope.progress = (scope.completed * 100) / scope.added;
            return Math.max(1, scope.progress);
          };

          scope.dz = new Dropzone(document.body, {
            url: "/upload",
            createImageThumbnails: false,
            parallelUploads: 4,
            previewsContainer: elements[0],
            clickable: document.getElementById('upload-files')
          });

          scope.dz.on("addedfile", function(file) {
            show_progress(true);

            scope.added++;

            window.onbeforeunload = function(e) {
              e = e || window.event;
              if (e) {
                e.returnValue = '';
              }
              return '';
            };

            if (scope.added === 1) {
              elem.setAttribute('style', 'width:1%');
              elem.innerHTML = 'Starting...';
              scope.$apply()
            }
          });

          var last = 0;
          var now;

          scope.dz.on("complete", function(progress) {
            scope.completed++;
            elem.setAttribute('style', 'width:' + scope.get_width() + '%')
            elem.innerHTML = scope.progress.toFixed(2) + '%';

            if (scope.completed === scope.added) {
              window.onbeforeunload = null;
              setTimeout(function() {
                location.reload();
              }, 1500);
            }
          });
        }
      };
    }
  };
});
