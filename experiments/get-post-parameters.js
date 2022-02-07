const express = require('express');

const app = express();
const host = process.env.HOST || 'localhost';
const port = process.env.PORT || 8718;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.post('/api/users', function(req, res) {
  const user_id = req.body.id;
  const token = req.body.token;
  const geo = req.body.geo;
  res.send({
    'user_id': user_id,
    'token': token,
    'geo': geo
  });
});

app.listen(port);
console.log(`server started at http://${host}:${port}`);
