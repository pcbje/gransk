var modules = angular.module('gransk.modules');


modules.filter('clean_whitespace', function() {
  return function(text) {
    if (!text) return '';

    return text.replace(/\n\s+\n/g, '\n').replace(/\ +/g, ' ').replace(/\t/g, ' ');
  };
});

modules.controller('DocumentsCtrl', function($scope, $location, $cookies, doc, hotkeys, config, format) {
  $scope.common_entities = {
    msg: null,
    hits: null
  };
  $scope.document_facets = {
    ext: {},
    doctype: {},
    tag: {}
  };
  $scope.index = $cookies.get('docindex') ? $cookies.get('docindex') * 1 : 0;
  $scope.$parent.mode = 'documents';
  $scope.lock_msg = false;
  $scope.docs = {
    hits: []
  };

  $scope.show = $cookies.get('ds') ? $cookies.get('ds') : 'text';

  var _maybe_load_text = function() {
    if ($scope.show == 'text') doc.load_text($scope.doc);
  };

  $scope.set_show = function(show) {
    $scope.show = show;
    $cookies.put('ds', show);
    _maybe_load_text();
  };

  $scope.search_meta = function(key, value, op, clear) {
    var add = 'meta.' + key + op + value;

    if ($scope.$parent.query_string && $scope.$parent.query_string.indexOf(add) >= 0) {
      return;
    }

    if (clear || !$scope.$parent.query_string) {
      $scope.$parent.query_string = '';
    }

    if ($scope.$parent.query_string.trim().length > 0) {
        $scope.$parent.query_string += ' AND ';
    }

    $scope.$parent.query_string += add;
    $location.search('lock', null);
    $cookies.put('q', $scope.$parent.query_string);
    $scope.$parent.submit_query($scope.$parent.query_string);
  };

  hotkeys.clear();
  hotkeys.listen(function(action) {
    var result = hotkeys.get(action, $scope.docs.hits.length, $scope.docs.pages, $scope.docs.page, $scope.index);

    if (!result) return;

    if (result.page >= 0) $scope.change_document_page(result.page, result.index);
    if (result.index >= 0) $scope.set_index(result.index);

    $scope.$apply();
  });

  $scope.$on('reset_search', function() {
    if ($scope.$parent.query_string.length > 0) {
      $scope.set_show('hits');
    }
    else if($scope.show == 'hits') {
      $scope.set_show('text');
    }

    $scope.document_facets = {
      doctype: {},
      ext: {},
      tag: {}
    };
  });

  $scope.$on('docs', function(e, docs) {
    $scope.docs = docs;
    $scope.doc = doc.get_document_by_index($scope.index);
    _maybe_load_text();
  });

  $scope.delete_doc = function(id, doc_id) {
    if (confirm('This will remove this document.')) {
      doc.delete(id, doc_id, function() {
        //location.reload();
      });
    }
  };

  $scope.set_index = function(index) {
    $scope.index = index;
    $scope.doc = doc.get_document_by_index(index);
    if ($scope.show == 'text') doc.load_text($scope.doc);
    $cookies.put('docindex', index);
  };

  if ($location.search().lock) {
    var q = 'id:' + encodeURIComponent($location.search().lock);
    if ($location.search().q) {
      q += ' AND ' +  $location.search().q;
    }
    $scope.$parent.submit_query(q);
    $scope.lock_msg = true;
    $scope.set_index(0);
  } else {
    $scope.$parent.submit_query($scope.$parent.query_string);
    $scope.set_index(0);
  }

  $scope.change_document_page = function(page, _index) {
    $scope.index = _index ? _index : 0;
    doc.search($scope.query_string, page, $scope.document_facets, function(docs) {
      $scope.docs = docs;
      $scope.doc = doc.get_document_by_index($scope.index);
      _maybe_load_text();
    });
  };

  $scope.$watch('doc', function() {
    $scope.aggregations = {};
    if ($scope.doc) $scope.set_title('Documents', $scope.doc._source.filename);
  })

  $scope.aggregations = {};
  $scope.aggregate_field =function(key) {
    if(key in $scope.aggregations) {
      delete $scope.aggregations[key];
      return;
    }

    doc.aggregate($scope.$parent.query_string, key, $scope.document_facets, function(result) {
      $scope.aggregations[key] = result;
    });
  }

  $scope.$watch('document_facets', function() {
    if ($location.search().lock) return;
    $cookies.putObject('df', $scope.document_facets);
    doc.search($scope.query_string, 0, $scope.document_facets, function(docs) {
      $scope.docs = docs;
      $scope.doc = doc.get_document_by_index($scope.index);
      _maybe_load_text();
    });
  }, true);

  $scope.obj_size = function(obj) {
    return Object.keys(obj).length;
  };

  $scope.load_document_children = function(page) {
    doc.load_children($scope.doc, page);
  };

  $scope.load_document_entities = function(entity_page) {
    doc.load_document_entities($scope.doc, entity_page);
  };
});

modules.service('doc', function($cookies, config, client, pagecount, aggs, related, query) {
  var query_error = '';
  var query_warning = '';
  var documents;

  var escape_reg_exp = function(str) {
    return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
  }

  return {
    set_docs: function(docs) {
      documents = docs;
    },
    load_children: function(_document, page) {
      page = Math.max(page, 0);
      if (_document.child_pages) page = Math.min(page, _document.child_pages);

      var size = 15;

      client.search({
        index: 'gransk',
        type: 'document',
        body: {
          size: size,
          from: size * page,
          _source: {
            excludes: ['text']
          },
          query: {
            nested: {
              path: 'parent',
              query: {
                bool: {
                  must: [{
                    match: {
                      'parent.id': _document._source.id
                    }
                  }]
                }
              }
            }
          }
        }
      }).then(function(resp) {
        _document.children = resp.hits;
        _document.child_pages = pagecount.compute(resp.hits.total, size);
        _document.child_page = page;
      });
    },

    get_document_by_index: function(index) {
      if (!documents) return;
      _document = documents.hits[index];
      if (!_document) return;

      this.load_related(_document);
      this.load_children(_document, 0);
      this.load_document_entities(_document, 0);

      return _document;
    },

    load_related: function(doc, callback) {
      related.load('document', doc._source.id, function(related) {
        _document.related = related;
      });
    },

    aggregate: function(query_string, field, facets, callback) {
      var obj = query.generate('document', 'text', query_string, ['text'], 0, facets);
      obj.body.aggs = {}
      obj.body.size = 0;
      delete obj.body.highlight;
      obj.body.aggs[field] = {
        nested : {
            path : 'meta'
        },
        aggs: {
          meta: {
            terms: {
              field: "meta." + field,
              size: 10
            }
          }
        }
      };

      client.search(obj).then(function(resp) {
        callback(resp.aggregations);
      });
    },

    delete: function(id, doc_id, callback) {
      var sendbulk = function(bulk, callback) {
        if (bulk.length > 0) {
          client.bulk({body: bulk}, function() {
            console.log('deleted ' + bulk.length + ' items.');
            callback();
          });
        }
        else {
          callback();
        }
      }

      client.search({
        index: 'gransk',
        type: 'in_doc',
        body: {
          size: 1000, from: 0,
          query: {match: {doc_id: doc_id}
          }
        }
      }).then(function(resp) {
        var entities = {}
        var bulk = [];

        bulk.push({ delete: { _index: 'gransk', _type: 'document', _id: id } });

        resp.hits.hits.map(function(in_doc) {
          bulk.push({ delete: { _index: 'gransk', _type: 'in_doc', _id: in_doc._id } });
          entities[in_doc._source.entity_id] = true;
        });

        client.bulk({body: bulk}, function() {
          var entity_bulk = []
          var remaining = 0;
          var deleted_entities = 0;
          if (Object.keys(entities).length === 0) {
            callback();
            return
          }

          for (var entity_id in entities) {
            remaining++;
            client.search({index: 'gransk',type: 'in_doc',body: {size: 1, from: 0,query: {match: {entity_id: entity_id}}}}).then(function(eresp) {
              if (eresp.hits.total === 0) {
                console.log("no more references to entity " + entity_id + " deleting.");
                client.search({index: 'gransk',type: 'entity',body: {size: 1, from: 0,query: {match: {entity_id: entity_id}}}}).then(function(ent) {
                  entity_bulk.push({ delete: { _index: 'gransk', _type: 'entity', _id: ent._id } })
                  remaining--;
                  if (remaining === 0) {
                    sendbulk(entity_bulk, callback)
                  }
                });
              }
              else {
                remaining--;
                if (remaining === 0) {
                  sendbulk(entity_bulk, callback)
                }
              }
            });
          }

        });
      });
    },

    search: function(query_string, page, facets, callback, override_size) {
      page = Math.max(page, 0);

      if (documents) {
        page = Math.min(page, documents.pages);
      }

      var obj = query.generate('document', 'text', query_string, ['text'], page, facets, override_size);

      var self = this;

      client.search(obj).then(function(resp) {
        documents = resp.hits;
        documents.page = page;
        documents.pages = pagecount.compute(documents.total);
        documents.facets = {
          extension: {},
          doctype: {},
          tag: {}
        };

        resp.aggregations.ext.buckets.map(function(bucket) {
          documents.facets.extension[bucket.key] = bucket.doc_count;
        });

        resp.aggregations.doctype.buckets.map(function(bucket) {
          documents.facets.doctype[bucket.key] = bucket.doc_count;
        });

        resp.aggregations.tag.buckets.map(function(bucket) {
          documents.facets.tag[bucket.key] = bucket.doc_count;
        });

        callback(documents);
      });
    },

    load_text: function(doc) {
      if (!doc) return;

      doc.doctext = 'Loading text...';

      var self = this;

      client.search({
        index: 'gransk',
        type: 'document',
        body: {
          size: 1,
          _source: {
            includes: ['text']
          },
          query: {
            match: {
              id: doc._source.id
            }
          }
        }
      }).then(function(resp) {
        doc.doctext_original = resp.hits.hits[0]._source.text.split(/\0/)[0];
        self.highlight_text(doc);
      });
    },

    highlight_text: function(_document) {
      _document.doctext = _document.doctext_original;
      if (!_document.doctext) return;
      if (!_document.entities) return;
      var cache = {};
      _document.entities.hits.map(function(entity) {
        if (entity._source.entity_value in cache) return;
        cache[entity._source.entity_value] = true;
        _document.doctext = _document.doctext.replace(
          new RegExp(escape_reg_exp(entity._source.entity_value), 'g'), function(res, i) {
            return '[[a href="#/entities?lock=' + entity._source.entity_id + '" class="entity"]]' + res + '[[/a]]'
          });
      });
    },

    load_document_entities: function(_document, page) {
      _document.entity_page = page;
      _document.entity_page = Math.max(_document.entity_page, 0);

      if (_document.entity_pages >= 0) {
        _document.entity_page = Math.min(_document.entity_page, _document.entity_pages);
      }

      var self = this;
      var size = 15;

      client.search({
        index: 'gransk',
        type: 'in_doc',
        body: {
          size: size,
          from: _document.entity_page * size,
          query: {
            match: {
              doc_id: _document._source.id
            }
          }
        }
      }).then(function(resp) {
        _document.entities = resp.hits;
        _document.entity_pages = pagecount.compute(_document.entities.total, size);
        self.highlight_text(_document);
      });
    }
  };
});
