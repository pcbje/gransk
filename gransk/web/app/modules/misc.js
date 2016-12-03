var modules = angular.module('gransk.modules');

modules.service('client', function($http, $q) {
  return {
    search: function(query) {
      return $q(function(resolve) {
        $http.get('/search?q=' + JSON.stringify(query)).then(function(resp) {
          resolve(resp.data);
        });
      })
    }
  }
});

modules.service('text_selection', function(config) {
  var listeners = [];
  var ignore_ids = {};

  window.addEventListener("mousedown", function(e) {
    window.getSelection().removeAllRanges();
  });

  window.addEventListener("mouseup", function(e) {
    var range;
    try {
      range = window.getSelection().getRangeAt(0);
    } catch (e) {return}

    var parent = range.commonAncestorContainer;
    var valid = false;
    while (parent) {
      try {
        if (parent.getAttribute('id') in ignore_ids) {
          return;
        }

        if (parent.getAttribute('class').indexOf('searchable') >= 0) {
          valid = true;
          break
        }
      } catch (e) {}
        parent = parent.parentNode;
    }

    var selected = null;
    if (valid) {
      selected = range.commonAncestorContainer.data.substring(range.startOffset, range.endOffset).trim();
      if (selected.length === 0) selected = null;
    }

    listeners.map(function(listener) {
      listener(selected);
    });
  });

  return {
    clear: function() {
      ignore_ids = {}
      listeners = [];
    },
    listen: function(ignore_id, callback) {
      ignore_ids[ignore_id] = true;
      listeners.push(callback);
    }
  }
});

modules.service('hotkeys', function(config) {
  var listeners = [];

  window.addEventListener("keydown", function(e) {
    if (document.activeElement.getAttribute('type') === 'text') return;
    var action = null;
    if (e.key === '<') {
      action = 'up';
    } else if (e.key === 'z') {
      action = 'down';
    } else if (e.key === 'n') {
      action = 'next';
    } else if (e.key === 'p') {
      action = 'prev';
    } else {
      return;
    }

    listeners.map(function(listener) {
      listener(action);
    });
  }, false);

  return {
    clear: function() {
      listeners = [];
    },
    listen: function(callback) {
      listeners.push(callback);
    },
    get: function(action, items, pages, page, index) {
      if (action === 'up') {
        if (index === 0 && page > 0) {
          return {
            page: page - 1,
            index: config.pagesize - 1
          };
        } else {
          return {
            index: Math.max(0, index - 1)
          };
        }
      } else if (action === 'down') {
        if (index === items - 1 && page < pages) {
          return {
            page: page + 1,
            index: 0
          };
        } else {
          return {
            index: Math.min(index + 1, items - 1)
          };
        }
      } else if (action === 'next' && page < pages) {
        return {
          page: page + 1,
          index: 0
        };
      } else if (action === 'prev' && page > 0) {
        return {
          page: page - 1,
          index: 0
        };
      }

      return {};
    }
  };
});

modules.service('pagecount', function(config) {
  return {
    compute: function(items, size) {
      size = size ? size : config.pagesize;
      var pages = Math.floor(items / size);
      if (items % size === 0) {
        pages--;
      }
      return Math.max(0, pages);
    }
  };
});

modules.service('aggs', function(config) {
  return {
    get: function(normal) {
      var aggs = {};

      config.aggregation_fields.map(function(field) {
        aggs[field] = {
          terms: {
            field: field,
            size: normal ? config.aggregation_size : 60
          }
        };
      });

      return aggs;
    }
  };
});

modules.service('related', function($http) {
  return {
    load: function(type, id, callback) {
      var related = {
        msg: 'Loading...',
        data: []
      };

      $http.get('/related?type=' + type + '&id=' + id).then(function(resp) {
        related = resp;
        related.data.map(function(rel, i) {
          rel.shared.map(function(str, j) {
            related.data[i].shared[j] = JSON.parse(str);
          });
        });
        callback(related);
      });
    },
  };
});

modules.service('query', function(config, aggs) {
  return {
    generate: function(type, field, query, exclude, page, facets, override_size) {
      var obj = {
        index: 'gransk',
        type: type,
        body: {
          size: override_size ? override_size : config.pagesize,
          from: page * config.pagesize,
          _source: {
            exclude: exclude
          },
          query: automagic.generate(query, field),
          highlight: {
            pre_tags: ["[[span]]"],
            post_tags: ["[[/span]]"],
            fields: {
              text: {
                fragment_size: config.fragment_size,
                number_of_fragments: config.number_of_fragments
              }
            }
          },
          aggs: aggs.get(!override_size)
        }
      };

      if (type === 'document') {
        obj.body.sort = { "meta.added": { order: "desc" }};
      }

      for (var facet in facets) {
        var term = {};
        term[facet] = [];
        for (var key in facets[facet]) {
          if (facets[facet][key]) {
            term[facet].push(key);
          }
        }
        if (term[facet].length > 0) {
          obj.body.query.bool.must.push({
            terms: term
          });
        }
      }

      return obj;
    }
  };
});
