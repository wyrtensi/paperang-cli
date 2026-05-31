"use strict";

const { spawnSync } = require("node:child_process");

function buildPipInstallArgs(packageSpec, extraArgs = []) {
  return [
    ["-m", "pip", "install", "--upgrade", ...extraArgs, packageSpec],
    [
      "-m",
      "pip",
      "install",
      "--force-reinstall",
      "--no-deps",
      ...extraArgs,
      packageSpec
    ]
  ];
}

function runPipInstall(candidate, packageSpec, extraArgs = []) {
  let result = { status: 0 };

  for (const args of buildPipInstallArgs(packageSpec, extraArgs)) {
    result = spawnSync(candidate.command, [...candidate.args, ...args], {
      stdio: "inherit",
      windowsHide: true
    });

    if (result.status !== 0) {
      return result;
    }
  }

  return result;
}

module.exports = {
  buildPipInstallArgs,
  runPipInstall
};
