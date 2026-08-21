export default {
  // Split the report by the Python version a test ran under. All four versions
  // write into one 'allure-results', so without this they are one undivided
  // set of results. The label comes from tests/conftest.py, which adds
  // allure.label("python_version", ...) to every collected item.
  //
  // The keys are environment *ids* and are validated: latin letters, digits,
  // underscores and hyphens only. A key like "Python 3.10" is rejected and
  // 'allure' exits non-zero before generating anything, so the readable form
  // goes in 'name'.
  environments: {
    "python-3-7": {
      name: "Python 3.7",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.7")
    },
    "python-3-8": {
      name: "Python 3.8",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.8")
    },
    "python-3-9": {
      name: "Python 3.9",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.9")
    },
    "python-3-10": {
      name: "Python 3.10",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.10")
    }
  }
};
