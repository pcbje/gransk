describe("entities", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var _config;
  var _entity;
  var _client;
  var _related;
  var _controller;
  var scope;
  var _hotkeys;
  var _location;

  beforeEach(inject(function(config, entity, client, related, $controller, $rootScope, hotkeys, $location) {
    _config = config;
    _entity = entity;
    _client = client;
    _related = related;
    _controller = $controller;
    _root_scope = $rootScope;
    _hotkeys = hotkeys;
    _location = $location;
  }));

  describe("entities controller", function() {

    beforeEach(inject(function(_$injector_) {
      scope = _root_scope.$new();
      scope.$parent.query_string = '';
      scope.$parent.submit_query = function() {};
      _controller('EntitiesCtrl', {
        $scope: scope
      });
      _hotkeys.clear();
      $injector = _$injector_;
      $httpBackend = $injector.get('$httpBackend');
      $httpBackend.when('GET', /^\/search*/).respond({})
    }));


    it('should get current entity when entities are loaded', function() {
      spyOn(_entity, 'set_by_index');
      spyOn(_entity, 'get_by_index').andReturn('mock-ent-1');

      scope.$broadcast('entities', ['mock-1', 'mock-2', 'mock-3']);

      var expected_entities = ['mock-1', 'mock-2', 'mock-3'];
      var actual_entities = scope.entities;
      expect(actual_entities).toEqual(expected_entities);

      var expected_entity = 'mock-ent-1';
      var actual_entity = scope.entity;
      expect(actual_entity).toEqual(expected_entity);
    });

    it('lock entity', function() {
      var calls = 0;
      scope.$parent.submit_query = function(query_string) {
        expect(query_string).toEqual('entity_id:4321');
        calls++;
      };
      spyOn(_location, 'search').andReturn({
        lock: '4321'
      });
      _controller('EntitiesCtrl', {
        $scope: scope
      });
      _hotkeys.clear();
      expect(calls).toEqual(1);
    });

    it('should listen to hotkeys', function() {
      _controller('EntitiesCtrl', {
        $scope: scope
      });
      spyOn(_hotkeys, 'get').andReturn({
        page: 0,
        index: 0
      });
      var evt = new CustomEvent("keydown");
      evt.key = '<';
      window.dispatchEvent(evt);
      expect(_hotkeys.get).toHaveBeenCalled();
    });

    it('should change entity page', function() {
      spyOn(_client, 'search').andCallFake(function(query) {
        return {
          then: function(callback) {
            callback({
              hits: {
                hits: []
              },
              aggregations: {
                type: {
                  buckets: []
                }
              }
            });
          }
        };
      });

      scope.query_string = 'mockmock';
      scope.change_entity_page(1, 0);
      expect(scope.show).toEqual('documents');
    });

    it('should do new search when facets are updated', function() {
      spyOn(_entity, 'set_by_index');
      spyOn(_entity, 'get_by_index').andReturn('mock-ent-1');
      spyOn(_entity, 'search').andCallFake(function(query, page, facets, callback) {
        var expected = {
          type: {
            test: true
          }
        };
        var actual = facets;
        expect(expected).toEqual(actual);
        callback(['mock', 'mock', 'mock']);
      });

      scope.entity_facets.type.test = true;
      scope.$apply();

      var expected_entities = ['mock', 'mock', 'mock'];
      var actual_entities = scope.entities;
      expect(actual_entities).toEqual(expected_entities);

      var expected_entity = 'mock-ent-1';
      var actual_entity = scope.entity;
      expect(actual_entity).toEqual(expected_entity);
    });
  });

  describe("entity service", function() {

    it('should search', function() {
      spyOn(_client, 'search').andReturn({
        then: function(callback) {
          callback({
            hits: {
              hits: [],
              total: 3,
            },
            aggregations: {
              type: {
                buckets: [{
                  key: 'mock',
                  doc_count: 2
                }]
              }
            }
          });
        }
      });

      _entity.search('search string here', 0, {}, function(entities) {
        var expected_entites = {
          hits: [],
          total: 3,
          page: 0,
          pages: 0,
          facets: {
            entity_type: {
              mock: 2
            }
          }
        };

        expect(expected_entites).toEqual(entities);
      });
    });

    it('should should get documents containing entity', function() {
      spyOn(_client, 'search').andCallFake(function(query) {
        expect(query.type).toEqual('in_doc');
        expect(query.body.query).toEqual({
          match: {
            entity_id: '1234'
          }
        });
        return {
          then: function(callback) {
            callback({
              hits: ['mock', 'mock', 'mock'],
              total: 4
            });
          }
        };
      });

      var entity = {
        _source: {
          entity_id: '1234'
        }
      };
      _entity.get_documents(entity, 0);

      expect(entity.documents).toEqual(['mock', 'mock', 'mock']);
    });

    it('should load related', function() {
      spyOn(_related, 'load').andCallFake(function(type, id, callback) {
        expect(type).toEqual("entity");
        expect(id).toEqual("mock");
        callback(['a', 'b', 'c']);
      });
      _entity.set_entities({
        hits: [{
          _source: {
            entity_id: 'mock'
          }
        }, {
          _source: {
            entity_id: 'other'
          }
        }]
      });
      entity = _entity.get_by_index(0);
      _entity.load_related(entity);

      expect(entity.related.length).toEqual(3);
    });

    it('should set entity', function() {
      spyOn(_entity, 'get_documents').andReturn({});
      spyOn(_entity, 'load_related').andReturn({});
      _entity.set_entities({
        hits: ['mock-1', 'mock-2', 'mock-3']
      });
      var expected_entity = 'mock-2';
      var actual_entity = _entity.set_by_index(1);
      expect(actual_entity).toEqual(expected_entity);
    });
  });

  describe("entities directives", function() {
    var $compile;

    beforeEach(inject(function($injector, _$compile_) {
      scope = _root_scope.$new();
      $compile = _$compile_;
      $httpBackend = $injector.get('$httpBackend');
      $httpBackend.when('GET', '/network?hops=1&entity_id=1234').respond({
        nodes: {
          'a': {
            value: 'a'
          },
          'b': {
            value: 'b'
          }
        },
        links: [
          ['a', 'b', 2]
        ]
      });
    }));

    afterEach(function() {
      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
    });

    it('should compile entity network', function() {
      $httpBackend.expectGET('/network?hops=1&entity_id=1234');
      scope.entity = {
        _source: {
          entity_id: 1234
        }
      };
      var element = $compile('<entitynetwork entity="entity"></entitynetwork>')(scope);
      scope.$apply();

      $httpBackend.flush();

      expect(element.html()).toContain('<svg>');
      expect(element.html()).toContain('<g ');
      expect(element.html()).toContain('<circle ');
    });
  });
});
