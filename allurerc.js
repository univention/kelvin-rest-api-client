export default {
  historyPath: "./allure-history.jsonl",
  environments: {
    "Python 3.7": {
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.7")
    },
    "Python 3.8": {
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.8")
    },
    "Python 3.9": {
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.9")
    },
    "Python 3.10": {
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.10")
    }
  }
};
