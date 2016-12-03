var modules = angular.module('gransk.modules');

modules.directive('quicklook', function(client, text_selection, $location) {

  return {
    restrict: 'E',
    templateUrl: '/static/views/quicklook.html',
    scope: {
      lock: '=',
      search: '&'
    },
    link: function(scope, element) {
      scope.active = false;

      scope.set_lock = function(id) {
        $location.search('lock', id);
      }

      var update_class = function(active) {
        angular.element(element[0]).children()[0].setAttribute('class', active ? 'active' : '');

        var update = document.getElementsByClassName("column-fill");

        for (var i=0; i<update.length; i++) {
          update.item(i).setAttribute('name', active ? 'withquick' : '')
        }
      }

      text_selection.listen('quicklook', function(text) {
        scope.documents = {};
        scope.entities = {};

        scope.quicklook = text;

        var active = text !== null;

        if (active) {
          update_class(active);
        }
        else {
          setTimeout(function() {
            update_class(active);
          }, 500);
        }

        if (active) {
          client.search({
            index: 'gransk',
            type: 'document',
            body: {
              _source: {exclude: ['text']},
              query: automagic.generate('*' + text.toLowerCase() + '*', 'text')
            }
          }).then(function(resp) {
            scope.documents = resp.hits;
          });

          client.search({
            index: 'gransk',
            type: 'entity',
            body: {query: automagic.generate('*' + text.toLowerCase() + '*', 'value')}
          }).then(function(resp) {
            scope.entities = resp.hits;
          });
        }
      })
    }
  };
});
