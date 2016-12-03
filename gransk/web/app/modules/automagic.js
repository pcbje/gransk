var automagic = (function() {
  var Field = function() {
    var rangeValues = {
      '>': 'gt',
      '<': 'lt',
      '>=': 'gte',
      '<=': 'lte'
    }

    var rsplit = function(string, sep, maxsplit) {
        var split = string.split(sep);
        return maxsplit ? [ split.slice(0, -maxsplit).join(sep) ].concat(split.slice(-maxsplit)) : split;
    }

    var getNestedObject = function(field) {
      var path = rsplit(field, '.', 1)
      var obj = {
        nested: {
          path: path[0],
          query: {}
        }
      }

      return [obj, obj.nested.query];
    }

    var getFieldObject = function(field) {
      var nested = field.indexOf('.') >= 0;
      if (nested) {
        return getNestedObject(field)
      }

      var obj = {};

      return [obj, obj]
    };

    return {
      equal: function(field, value) {
        var queryType = value.indexOf('*') < 0 ? 'match' : 'wildcard';

        if (value.indexOf(' ') >= 0 || value.indexOf('-') >= 0) {
          queryType = 'match_phrase';
        }

        var parts = getFieldObject(field);
        var body = parts[0];
        var query = parts[1];

        query[queryType] = {};
        query[queryType][field] = value;

        return body;
      },
      range: function(field, value, op) {
        var rangeKey = rangeValues[op];

        var parts = getFieldObject(field);
        var body = parts[0];
        var query = parts[1];

        query.range = {};
        query.range[field] = {};
        query.range[field][rangeKey] = isNaN(value * 1) ? value : value * 1;

        return body;
      }
    }
  }

  var Body = function(defaultfield) {
    var operatorParsers = {
      ':': 'equal',
      '>': 'range',
      '<': 'range',
      '>=': 'range',
      '<=': 'range'
    }

    var parseClause = function(clause) {
      if (clause.length === 0) {
        return {
          match_all: {}
        }
      }
      var operators = Object.keys(operatorParsers);

      operators.sort(function(a, b) {
        return b.length - a.length;
      })

      var field = new Field();

      var ops = clause.match(new RegExp(operators.join('|'), 'g'));

      if (ops === null) {
        return field['equal'](defaultfield, clause);
      }

      if (ops.length > 1) {
        throw "Clause may only contain a single operator";
      }

      var op = ops[0];

      var parts = clause.split(op);
      var fieldname = parts[0].trim();
      var value = parts[1].trim();

      return field[operatorParsers[op]](fieldname, value, op)
    };

    var clauses = {
        bool: {
          must: []
        }
    };

    return {
      addClause: function(clause) {
        clauses.bool.must.push(parseClause(clause));
      },
      asJson: function() {
        return JSON.parse(JSON.stringify(clauses))
      }
    }
  };

  var Automagic = function() {
    return {
      generate: function(string, defaultfield) {
        if (!defaultfield) defaultfield = '_all';

        var body = new Body(defaultfield);

        var clauses = string.trim().split(' AND ');

        clauses.map(function(clause) {
          body.addClause(clause.trim());
        });

        return body.asJson();
      }
    }
  };

  return new Automagic();
})();
