"use strict";

const { spawn, spawnSync } = require("node:child_process");

const packageJson = require("../package.json");

function getPythonCandidates(platform = process.platform) {
  if (platform === "win32") {
    return [
      { command: "py", args: ["-3"] },
      { command: "python", args: [] },
      { command: "python3", args: [] }
    ];
  }

  return [
    { command: "python3", args: [] },
    { command: "python", args: [] }
  ];
}

function getMinimumPythonVersion() {
  return packageJson.paperangCli.pythonMinimumVersion;
}

function findPython(candidates = getPythonCandidates()) {
  const versionParts = getMinimumPythonVersion().split(".").map(Number);
  const check = `import sys; raise SystemExit(0 if sys.version_info >= (${versionParts.join(", ")}) else 1)`;

  for (const candidate of candidates) {
    const result = spawnSync(
      candidate.command,
      [...candidate.args, "-c", check],
      { encoding: "utf8", windowsHide: true }
    );

    if (result.status === 0) {
      return candidate;
    }
  }

  return null;
}

function buildPythonInvocation(candidate, userArgs) {
  return {
    command: candidate.command,
    args: [...candidate.args, "-m", "paperang_cli", ...userArgs]
  };
}

function getPythonPackageSpec() {
  return `paperang-cli==${packageJson.paperangCli.pythonPackageVersion}`;
}

function runPaperang(userArgs, stdio = "inherit") {
  const candidate = findPython();

  if (!candidate) {
    console.error(`paperang-cli requires Python ${getMinimumPythonVersion()} or newer.`);
    console.error(`Install Python, then run: python -m pip install --upgrade ${getPythonPackageSpec()}`);
    return 1;
  }

  const invocation = buildPythonInvocation(candidate, userArgs);
  const child = spawn(invocation.command, invocation.args, { stdio, windowsHide: false });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }

    process.exit(code ?? 1);
  });

  child.on("error", (error) => {
    console.error(error.message);
    process.exit(1);
  });

  return 0;
}

module.exports = {
  buildPythonInvocation,
  findPython,
  getMinimumPythonVersion,
  getPythonCandidates,
  getPythonPackageSpec,
  runPaperang
};
