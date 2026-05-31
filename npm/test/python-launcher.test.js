"use strict";

const assert = require("node:assert/strict");
const versionManifest = require("../../src/paperang_cli/version-manifest.json");
const test = require("node:test");

const {
  buildPythonInvocation,
  getPythonCandidates,
  getPythonPackageSpec
} = require("../lib/python-launcher");
const { buildPipInstallArgs } = require("../lib/python-installer");

test("Windows prefers the py launcher", () => {
  assert.deepEqual(getPythonCandidates("win32"), [
    { command: "py", args: ["-3"] },
    { command: "python", args: [] },
    { command: "python3", args: [] }
  ]);
});

test("other platforms prefer python3", () => {
  assert.deepEqual(getPythonCandidates("linux"), [
    { command: "python3", args: [] },
    { command: "python", args: [] }
  ]);
});

test("Python package version matches the npm wrapper version", () => {
  assert.equal(getPythonPackageSpec(), `paperang-cli==${versionManifest.version}`);
});

test("launcher forwards CLI arguments through the Python module", () => {
  assert.deepEqual(
    buildPythonInvocation(
      { command: "py", args: ["-3"] },
      ["--json", "config", "show"]
    ),
    {
      command: "py",
      args: ["-3", "-m", "paperang_cli", "--json", "config", "show"]
    }
  );
});

test("pip install sequence replaces same-version editable installs", () => {
  assert.deepEqual(
    buildPipInstallArgs("paperang-cli==0.1.5", ["--user"]),
    [
      ["-m", "pip", "install", "--upgrade", "--user", "paperang-cli==0.1.5"],
      [
        "-m",
        "pip",
        "install",
        "--force-reinstall",
        "--no-deps",
        "--user",
        "paperang-cli==0.1.5"
      ]
    ]
  );
});
