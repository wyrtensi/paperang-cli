#!/usr/bin/env node
"use strict";

const { runPaperang } = require("../lib/python-launcher");

process.exitCode = runPaperang(process.argv.slice(2));
