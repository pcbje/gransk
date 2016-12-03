var modules = angular.module('gransk.modules');

modules.service('format', function() {
  return {
    size: function(size) {
      if (size < 1024) {
        return size + ' bytes';
      }

      size /= 1024;

      if (size < 1024) {
        return size.toFixed(1) + ' KB';
      }

      size /= 1024;

      if (size < 1024) {
        return size.toFixed(1) + ' MB';
      }

      size /= 1024;

      if (size < 1024) {
        return size.toFixed(1) + ' GB';
      }
    },

    padd: function(value) {
      if (value < 10) return '0' + value;
      return value;
    },

    time: function(now, date) {
      var now_unix = now.getTime() / 1000;
      var then_unix = date.getTime() / 1000;

      if (now_unix - then_unix < 60) {
        return (now_unix - then_unix).toFixed(0) + ' seconds ago';
      }

      if (now_unix - then_unix < 60 * 60) {
        return ((now_unix - then_unix) / 60).toFixed(0) + ' minutes ago';
      }

      if (now_unix - then_unix < 60 * 60 * 24) {
        return ((now_unix - then_unix) / (60  * 60)).toFixed(0) + ' hours ago';
      }

      if (now_unix - then_unix < 60 * 60 * 24 * 7) {
        return ((now_unix - then_unix) / (60 * 60 * 24)).toFixed(0) + ' days ago';
      }

      return date.getFullYear() + '-' + this.padd(date.getMonth() + 1) + '-' + this.padd(date.getDate()) + ' ' + this.padd(date.getHours()) + ':' + this.padd(date.getMinutes()) + ':' + this.padd(date.getSeconds());
    },

    auto: function(key, value) {
      if (value instanceof Object) {
        var arr = [];
        for (var x in value) {
          arr.push(x.replace(/\0/g, '.'));
        }
        arr.sort();
        return arr.join('\n');
      }

      if (key.toLowerCase().indexOf('time') >= 0 || key.toLowerCase().indexOf('date') >= 0) {
        var test_datestr_year = new Date(value).getFullYear();
        if (test_datestr_year > 1980 && test_datestr_year < 2037) {
          var now = new Date();
          return this.time(now, new Date(value));
        }
      }

      if (!isNaN(value*1)) {
        value *= 1;

        if (key.toLowerCase().indexOf('size') >= 0) {
          return this.size(value);
        }

        var test_unix_year = new Date(value * 1000).getFullYear();

        if (test_unix_year > 1980 && test_unix_year < 2037) {
          var now = new Date();
          return this.time(now, new Date(value * 1000));
        }
      }

      return value;
    }
  }
});
