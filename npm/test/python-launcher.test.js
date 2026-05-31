"use strict";

const assert = require("node:assert/strict");
const versionManifest = require("../../src/paperang_cli/version-manifest.json");
const test = require("node:test");

const {
  buildPythonInvocation,
  getPythonCandidates,
  getPythonPackageSpec
} = require("../lib/python-launcher");

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
