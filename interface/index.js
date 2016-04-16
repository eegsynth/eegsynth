var express = require('express')
var app = express();

var http = require('http')
var spawnSync = require('child_process').spawnSync;
var execSync = require('child_process').execSync;
var path = require('path');
var fs = require('fs');
var bodyParser = require('body-parser');
var cookieParser = require('cookie-parser');
var session = require('express-session');
var async = require('async');

app.use(express.static(__dirname + '/public'));

var Redis = require('ioredis');
var redis = new Redis(6379, 'localhost');

// app.use(cookieParser('secret'));
// app.use(session({cookie: { maxAge: 60000 }}));
// app.use(flash());

app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'jade');

// parse application/x-www-form-urlencoded
app.use(bodyParser.urlencoded({ extended: false }))
app.use(bodyParser.text())

// gzip/deflate outgoing responses
var compression = require('compression')
app.use(compression());

// store session state in browser cookie
var cookieSession = require('cookie-session')
app.use(cookieSession({
    keys: ['EeC9qua7aem1', 'hieGh0lo1oor']
}))

// parse urlencoded request bodies into req.body
// app.use(bodyParser.urlencoded({ extended: true }))

function moduleCommand(name, command) {
  switch (command) {
    case 'start':
    case 'stop':
    case 'restart':
    case 'status':
      // construct the command line
      var filename = path.join(__dirname, '..', 'module', name, name + '.sh');
      console.log(filename + " " + command);
      var output = spawnSync(filename, [command], {timeout: 5000});
      return output.stdout.toString();
      break;

    case 'log':
      return 'failed';
      break;

    case 'edit':
      return 'failed';
      break;

    default:
      return 'failed';
  }
}

app.get('/', function(req, res, next) {
  res.render('index.jade');
  next();
});

// log
app.get('/*/log', function (req, res, next) {
  var name    = req.url.split('/')[1];
  var command = req.url.split('/')[2];
  var filename = path.join(__dirname, '..', 'module', name, name + '.log');
  fs.stat(filename, function (err, stats) {
    if (err) {
      res.render('log.jade', {
        form_filename: filename,
        form_content: ''
      });
      next();
    }
    else {
      var content = fs.readFileSync(filename, {encoding: 'utf8'});
      res.render('log.jade', {
        form_filename: filename,
        form_content: content
      });
      next();
    }
  });
});
app.post('/*/log', function (req, res, next) {
  // nothing happens on a POST
  res.status(200);
  res.redirect('/');
});

// edit
app.get('/*/edit', function (req, res, next) {
  var name    = req.url.split('/')[1];
  var command = req.url.split('/')[2];
  var filename = path.join(__dirname, '..', 'module', name, name + '.ini');
  if (fs.lstatSync(filename).isFile())
    var content = fs.readFileSync(filename, {encoding: 'utf8'});
  else
    var content = '';
  res.render('edit.jade', {
      form_filename: filename,
      form_content: content
  });
  next();
});
app.post("/*/edit", function(req, res, next) {
  var name = req.url.split('/')[1];
  if (req.body.form_button == 'save') {
    fs.writeFileSync(req.body.form_filename, req.body.form_content, {encoding: 'utf8'});
    res.render('message.jade', {
      message_text: 'Saved '+ name + ' settings to file'
    });
  }
  else {
    // cancel
    res.status(200);
    res.redirect('/');
  }
  next();
});

// status, start, stop, restart
app.use('/*/status', function(req, res, next) {
  var name    = req.baseUrl.split('/')[1];
  var command = req.baseUrl.split('/')[2];
  res.render('message.jade', {
    message_text: moduleCommand(name, command)
  });
  next();
});

app.use('/*/start', function(req, res, next) {
  var name    = req.baseUrl.split('/')[1];
  var command = req.baseUrl.split('/')[2];
  res.render('message.jade', {
      message_text: moduleCommand(name, command)
  });
  next();
});

app.use('/*/stop', function(req, res, next) {
  var name    = req.baseUrl.split('/')[1];
  var command = req.baseUrl.split('/')[2];
  res.render('message.jade', {
      message_text: moduleCommand(name, command)
  });
  next();
});

app.use('/*/restart', function(req, res, next) {
  var name    = req.baseUrl.split('/')[1];
  var command = req.baseUrl.split('/')[2];
  res.render('message.jade', {
      message_text: moduleCommand(name, command)
  });
  next();
});

app.use('/monitor', function (req, res, next) {
  // Create a readable stream (object mode)
  var stream = redis.scanStream();
  var keys = [];
  stream.on('data', function (someKeys) {
    for (var i = 0; i < someKeys.length; i++) {
      keys.push(someKeys[i]);
    }
  });
  stream.on('end', function () {
    var body = [];
    async.each(keys,
      function(key, callback) {
        redis.get(key, function (err, result) {
          body.push({
            key: key,
            val: result
          });
          callback();
        });
      },
      function (err) {
        body.sort(function (a, b) {
          return (a.key).localeCompare(b.key);
        });
        res.render('monitor', {redis: {keyval : body}});
      }
    );
  });
});

app.post('/test', function (req, res, next) {
    //res.send(JSON.stringify(req.body, null, 2));
    res.setHeader('Content-Type', 'text/plain')
    res.write('you posted:\n\n')
    res.write(req.body.title)
    res.write(req.body.description)
    res.end()
    next();
});

//create node.js http server and listen on port
http.createServer(app).listen(3000)
