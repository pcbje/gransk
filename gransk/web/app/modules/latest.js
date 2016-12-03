var modules = angular.module('gransk.modules');

modules.controller('LatestCtrl', function($scope, $localStorage, client, config, doc) {
    $scope.$parent.mode = 'latest';

    $scope.document_facets = {
      doctype: {},
      ext: {},
      tag: {}
    };

    $scope.rem_active = function(key) {
        delete $scope.actives[key];
    }

    $scope.to_arr = function(obj) {
        var arr = [];
        for (var key in obj) {
            arr.push({
                key: key,
                value: obj[key]
            })
        }
        return arr;
    }

    var is_empty = function(obj) {
        for (var key in obj) {
            if (Object.keys(obj[key]).length > 0) {
                return false;
            }
        }
        return true;
    }

    $scope.full_facets = null;

    $scope.counts = {};
    $scope.actives = {};
    $scope.filled = {};
    $scope.new = {};

    var refresh = function(callback) {
        var totnew = 0;
        doc.search('', 0, $scope.document_facets, function(latest) {
            $scope.filled = {};

            if (is_empty($scope.document_facets)) {
                $scope.full_facets = {
                    tag: $scope.to_arr(latest.facets.tag),
                    extension: $scope.to_arr(latest.facets.extension),
                    doctype: $scope.to_arr(latest.facets.doctype)
                }
            }

            $scope.full_facets.tag.map(function(obj) {
                if (!(obj.key in $scope.counts)) {
                    $scope.counts[obj.key] = obj.value;
                }

                if (obj.key in latest.facets.tag) {
                    $scope.filled[obj.key] = obj.value;
                }

                if (obj.value > $scope.counts[obj.key]) {
                    $scope.actives[obj.key] = obj.value - $scope.counts[obj.key];
                    $scope.counts[obj.key] = obj.value;
                }

                totnew += $scope.actives[obj.key] ? $scope.actives[obj.key] : 0;
            });

          $scope.set_title_number('Latest', totnew);
          $scope.latest = latest;
          if (callback) callback();
      }, 30);
    }

    $scope.$watch('document_facets', function() {
        refresh();
    }, true);

    setInterval(function() {
        refresh(function() {

        })
    }, 5000);
});
