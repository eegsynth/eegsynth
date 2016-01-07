var express = require('express')
var http = require('http')
var spawnSync = require('child_process').spawnSync;
var execSync = require('child_process').execSync;
var path = require('path');
var fs = require('fs');
var bodyParser = require('body-parser');
var cookieParser = require('cookie-parser');
var session = require('express-session');
var app = express();

app.use(express.static(__dirname + '/public'));

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
    keys: ['secret1', 'secret2']
}))

// parse urlencoded request bodies into req.body
// app.use(bodyParser.urlencoded({ extended: true }))

function moduleCommand(name, command) {
  var allowedModules = ['buffer', 'devirtualizer', 'eeg', 'emg', 'endorphines', 'eyeblink', 'heartbeat', 'heartrate', 'keyboard', 'launchcontrol', 'openbci2ft', 'pulsegenerator', 'redis', 'sequencer', 'synthesizer', 'virtualizer'];

  // ensure that the module is correct
  okModule = false;
  for (i=0; i<allowedModules.length; i++) {
    if (name==allowedModules[i]) {okModule = true; break;}
  }
  if (!okModule) {
    console.log('incorrect module name: ' + name);
    return 'failed ' + name;
  }

switch (command) {
  case 'start':
  case 'stop':
  case 'restart':
  case 'status':
    // construct the command line
    var filename = path.join(__dirname, '..', 'module', name, name + '.sh');
    var output = spawnSync(filename, [command], {timeout: 5000});
    return output.stdout.toString();
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

app.post('/test', function (req, res) {
    //res.send(JSON.stringify(req.body, null, 2));
    res.setHeader('Content-Type', 'text/plain')
    res.write('you posted:\n\n')
    res.write(req.body.title)
    res.write(req.body.description)
    res.end()
});

// edit
app.get('/*/edit', function (req, res, next) {
  var name    = req.url.split('/')[1];
  var command = req.url.split('/')[2];
  var filename = path.join(__dirname, '..', 'module', name, name + '.ini');
  var content = fs.readFileSync(filename, {encoding: 'utf8'});
  res.render('edit.jade', {
      form_filename: filename,
      form_content: content
  });
  next();
});

app.post("/*/edit", function(req, res) {
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

// app.use('/', express.static(__dirname + '/public'));

/*
app.all('/', function (req, res, next) {
  var filename = __dirname + '/public/index.html';
  var txt = fs.readFileSync(filename, {encoding: 'utf8'});
  res.send(txt);
  next();
});
*/

//create node.js http server and listen on port
http.createServer(app).listen(3000)
