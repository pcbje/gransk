describe("stats", function() {
  beforeEach(module('gransk.modules'));
  beforeEach(module('gransk'));

  var _config;
  var _stats;
  var _client;
  var $compile;
  var _scope;
  var $timeout;


  beforeEach(inject(function(config, stats, client, _$compile_, $rootScope, _$timeout_, _$q_) {
    _config = config;
    _stats = stats;
    _client = client;
    $compile = _$compile_;
    $timeout = _$timeout_;
    _scope = $rootScope.$new();
    $q = _$q_;
  }));

  it('should generate statistics', function() {
    spyOn(_client, 'search').andReturn({
      then: function(callback) {
        callback({
          aggregations: {
            entities: {
              value: 10
            },
            documents: {
              value: 10
            },
            raw_entity: {
              buckets: [{
                key: '{"id": "mock", "value": "dummy"}',
                doc_count: 2
              }]
            },
            dummy_type: {
              buckets: [{
                key: 'mock',
                doc_count: 3
              }]
            }
          }
        });
      }
    });
    _stats.load(function(stats) {
      var expected_counts = ['entities', 'documents'];
      var expected_aggs = ['raw_entity', 'dummy_type'];
      expect(expected_counts).toEqual(Object.keys(stats.counts));
      expect(expected_aggs).toEqual(Object.keys(stats.aggs));
    });
  });

  it('should compile pie directive', function() {
    _scope.key = 'dummy';
    _scope.pid = 'dummy';
    _scope.data = {
      buckets: [{
        key: 'a',
        doc_count: 3
      }, {
        key: 'b',
        doc_count: 1
      }]
    };
    var element = $compile('<pie data="data" pid="key"></pie>')(_scope);
    _scope.$apply();

    expect(element.html()).toContain('dummy');

    expect(element.isolateScope().content.length).toEqual(2);
  });
});
