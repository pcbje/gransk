describe("docs", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var _config;
  var _doc;
  var _client;
  var _related;
  var _controller;
  var scope;
  var _hotkeys;
  var _location;

  beforeEach(inject(function(config, doc, client, related, $controller, $rootScope, hotkeys, $location) {
    _config = config;
    _doc = doc;
    _client = client;
    _related = related;
    _controller = $controller;
    _root_scope = $rootScope;
    _hotkeys = hotkeys;
    _location = $location;
  }));

  describe("doc controller", function() {

    beforeEach(function() {
      scope = _root_scope.$new();
      scope.$parent.submit_query = function() {};
      _controller('DocumentsCtrl', {
        $scope: scope
      });
      _hotkeys.clear();
    });

    it('should set show tab', function() {
      scope.set_show('mock');
      expect(scope.show).toEqual('mock');
    });

    it('should change document page', function() {
      spyOn(_doc, 'get_document_by_index').andReturn('mock-doc');
      spyOn(_doc, 'search').andCallFake(function(query, page, facets, callback) {
        expect(query).toEqual('mock');
        callback(['mock', 'mock', 'mock']);
      });
      scope.query_string = 'mock';
      scope.change_document_page(1, 0);

      var expected = ['mock', 'mock', 'mock'];
      var actual = scope.docs;
      expect(expected).toEqual(actual);

      var expected_doc = 'mock-doc';
      var actual_doc = scope.doc;
      expect(expected_doc).toEqual(actual_doc);
    });

    it('should return object size', function() {
      var expected = 2;
      var actual = scope.obj_size({
        'a': 1,
        'b': 2
      });
      expect(expected).toEqual(actual);
    });

    it('should get current doc when docs are loaded', function() {
      spyOn(_doc, 'get_document_by_index').andReturn('mock-doc-1');
      scope.$broadcast('docs', ['mock-1', 'mock-2', 'mock-3']);

      var expected_docs = ['mock-1', 'mock-2', 'mock-3'];
      var actual_docs = scope.docs;
      expect(expected_docs).toEqual(actual_docs);

      var expected_doc = 'mock-doc-1';
      var actual_doc = scope.doc;
      expect(expected_doc).toEqual(actual_doc);
    });

    it('searches document by meta field', function() {
        scope.$parent.submit_query = function(query_string) {
          expect(query_string).toEqual('meta.test<>value');
        };

        scope.search_meta('test', 'value', '<>', false)
    });

    it('does not add meta field if value already in query', function() {
        var calls = 0;
        scope.$parent.submit_query = function(query_string) {
          calls++;
        };

        scope.search_meta('field', 'value', ':', false)
        scope.search_meta('field', 'value', ':', false)
        expect(calls).toEqual(1);
    });

    it('clears query', function() {
        var calls = 0;
        var query = null;
        scope.$parent.submit_query = function(query_string) {
          query = query_string;
          calls++;
        };

        scope.search_meta('field', 'value1', ':', false);
        scope.search_meta('field', 'value2', ':', true);
        expect(calls).toEqual(2);
        expect(query).toEqual('meta.field:value2')
    });

    it('combines query clauses', function() {
        var calls = 0;
        var query = null;
        scope.$parent.submit_query = function(query_string) {
          query = query_string;
          calls++;
        };

        scope.search_meta('field', 'value1', ':', false);
        scope.search_meta('field', 'value2', ':', false);
        expect(calls).toEqual(2);
        expect(query).toEqual('meta.field:value1 AND meta.field:value2')
    });

    it('lock document', function() {
      var calls = 0;
      scope.$parent.submit_query = function(query_string) {
        expect(query_string).toEqual('id:1234');
        calls++;
      };
      spyOn(_location, 'search').andReturn({
        lock: '1234'
      });
      _controller('DocumentsCtrl', {
        $scope: scope
      });
      _hotkeys.clear();
      expect(calls).toEqual(1);
    });

    it('should listen to hotkeys', function() {
      _controller('DocumentsCtrl', {
        $scope: scope
      });
      spyOn(_hotkeys, 'get');
      var evt = new CustomEvent("keydown");
      evt.key = '<';
      window.dispatchEvent(evt);
      expect(_hotkeys.get).toHaveBeenCalled();
    });

    it('should do new search when facets are updated', function() {
      scope.set_title = function() {}
      spyOn(_doc, 'get_document_by_index').andReturn({_source: {filename: 'mock-doc'}});
      spyOn(_doc, 'search').andCallFake(function(query, page, facets, callback) {
        var expected = {
          ext: {
            test: true
          },
          doctype: {

          },
          tag: {

          }
        };
        var actual = facets;
        expect(expected).toEqual(actual);
        callback(['mock', 'mock', 'mock']);
      });

      scope.document_facets.ext.test = true;
      scope.$apply();

      var expected_docs = ['mock', 'mock', 'mock'];
      var actual_docs = scope.docs;
      expect(expected_docs).toEqual(actual_docs);

      var expected_doc = {_source: {filename: 'mock-doc'}};
      var actual_doc = scope.doc;
      expect(expected_doc).toEqual(actual_doc);
    });

    it('should not do new search when facets are updated if lock', function() {
      spyOn(_doc, 'search');
      _location.search('lock', 'test');
      scope.document_facets.ext.test = true;
      scope.$apply();
      expect(_doc.search).not.toHaveBeenCalled();
    });
  });

  describe("doc service", function() {
    it('should return document by index', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: {}
          });
        }
      });
      _doc.set_docs({
        hits: [{
          _source: {
            id: 'mock'
          }
        }, {
          _source: {
            id: 'other'
          }
        }]
      });
      doc = _doc.get_document_by_index(0);
      expect(doc._source.id).toEqual('mock');
    });

    it('should load related', function() {
      spyOn(_related, 'load').andCallFake(function(type, id, callback) {
        expect(type).toEqual("document");
        expect(id).toEqual("mock");
        callback(['a', 'b', 'c']);
      });
      _doc.set_docs({
        hits: [{
          _source: {
            id: 'mock'
          }
        }, {
          _source: {
            id: 'other'
          }
        }]
      });
      doc = _doc.get_document_by_index(0);
      _doc.load_related(doc);

      expect(doc.related.length).toEqual(3);
    });

    it('should aggregate', function() {
      var aggs;
      spyOn(_client, 'search').andCallFake(function(query) {
        aggs = query.body.aggs;
        return {
          then: function(callback) {
            callback({hits: {}})
          }
        }
      });

      _doc.aggregate('search string here', 'metafield', {}, function(docs) {});

      expect(aggs).toEqual({
        metafield : {
          nested : { path : 'meta' },
          aggs : { meta : {
            terms : { field : 'meta.metafield', size : 10 }
          } }
        } })
    });

    it('should search', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: {
              hits: [],
              total: 3,
            },
            aggregations: {
              ext: {
                buckets: [{
                  key: 'dummy',
                  doc_count: 2
                }]
              },
              doctype: {
                buckets: [{
                  key: 'dummy',
                  doc_count: 1
                }]
              },
              tag: {
                buckets: [{
                  key: 'dummy',
                  doc_count: 3
                }]
              }
            }
          });
        }
      });

      _doc.search('search string here', 0, {}, function(docs) {
        var expected_docs = {
          hits: [],
          total: 3,
          page: 0,
          pages: 0,
          facets: {
            extension: {
              dummy: 2
            },
            doctype: {
              dummy: 1
            },
            tag: {
              dummy: 3
            }
          }
        };

        expect(expected_docs).toEqual(docs);
      });
    });

    it('should load text', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: {
              hits: [{
                _source: {
                  text: 'mock entity mock'
                }
              }]
            }
          });
        }
      });

      var doc = {
        _source: {
          id: 'mock'
        },
        entities: {
          hits: [{
            _source: {
              entity_id: 'mock',
              entity_value: 'entity'
            }
          }]
        }
      };

      _doc.load_text(doc);

      var expected_original = 'mock entity mock';
      var expected_highlighted = 'mock [[a href="#/entities?lock=mock" class="entity"]]entity[[/a]] mock';

      expect(expected_original).toEqual(doc.doctext_original);
      expect(expected_highlighted).toEqual(doc.doctext);
    });

    it('should load document entities', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: {
              hits: [{
                entity_id: 'mock',
                entity_value: 'mock-value'
              }],
              total: 90
            }
          });
        }
      });

      var doc = {
        _source: {
          id: 'mock'
        }
      };

      _doc.load_document_entities(doc);

      expect(doc.entities.hits.length > 0).toBeTruthy();
      expect(doc.entity_pages > 0).toBeTruthy();
    });

    it('should load document children', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: 'mock'
          });
        }
      });

      var doc = {
        _source: {
          id: 'mock'
        }
      };

      _doc.load_children(doc);

      var expected = 'mock';
      expect(expected).toEqual(doc.children);
    });
  });
});
