export default {
  historyPath: "./allure-history.jsonl",
  environments: {
    "python-3-7": {
      title: "Python 3.7",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.7")
    },
    "python-3-8": {
      title: "Python 3.8",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.8")
    },
    "python-3-9": {
      title: "Python 3.9",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.9")
    },
    "python-3-10": {
      title: "Python 3.10",
      matcher: ({ labels }) =>
        labels.some(l => l.name === "python_version" && l.value === "3.10")
    }
  }
};
