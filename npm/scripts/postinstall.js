#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");

const {
  findPython,
  getMinimumPythonVersion,
  getPythonPackageSpec
} = require("../lib/python-launcher");

const candidate = findPython();
const packageSpec = getPythonPackageSpec();

if (!candidate) {
  console.error(`paperang-cli requires Python ${getMinimumPythonVersion()} or newer.`);
  console.error(`Install Python, then run: python -m pip install --upgrade ${packageSpec}`);
  process.exit(1);
}

function runPip(extraArgs) {
  return spawnSync(
    candidate.command,
    [...candidate.args, "-m", "pip", "install", "--upgrade", ...extraArgs, packageSpec],
    { stdio: "inherit", windowsHide: true }
  );
}

let result = runPip([]);

if (result.status !== 0) {
  console.warn("Global pip install failed; retrying with --user.");
  result = runPip(["--user"]);
}

if (result.status !== 0) {
  console.error(`Failed to install ${packageSpec}.`);
  process.exit(result.status || 1);
}
