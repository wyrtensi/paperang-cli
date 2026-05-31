#!/usr/bin/env node
"use strict";

const {
  findPython,
  getMinimumPythonVersion,
  getPythonPackageSpec
} = require("../lib/python-launcher");
const { runPipInstall } = require("../lib/python-installer");

const candidate = findPython();
const packageSpec = getPythonPackageSpec();

if (!candidate) {
  console.error(`paperang-cli requires Python ${getMinimumPythonVersion()} or newer.`);
  console.error(`Install Python, then run: python -m pip install --upgrade ${packageSpec}`);
  process.exit(1);
}

let result = runPipInstall(candidate, packageSpec);

if (result.status !== 0) {
  console.warn("Global pip install failed; retrying with --user.");
  result = runPipInstall(candidate, packageSpec, ["--user"]);
}

if (result.status !== 0) {
  console.error(`Failed to install ${packageSpec}.`);
  process.exit(result.status || 1);
}
