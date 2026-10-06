// Fixture de regresión BUG-scope de security_config: hay una entrada HTTP
// candidata (app.use) pero NINGUNA cabecera de seguridad. Con el bug presente
// esto lanzaba `NameError: name 'h' is not defined` y el detector no emitía
// el hecho de ausencia de cabeceras (Art. 25(2)).
const express = require("express");
const app = express();

app.use(express.json());

app.listen(3000, "0.0.0.0");