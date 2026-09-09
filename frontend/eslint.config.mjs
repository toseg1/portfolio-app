import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import reactPlugin from "eslint-plugin-react";

const config = [
  ...nextCoreWebVitals,
  {
    plugins: { react: reactPlugin },
    rules: {
      "react/jsx-no-literals": [
        "error",
        { allowedStrings: [".", ",", ":", "-", "/", "(", ")", "%", "€", "&"] },
      ],
    },
  },
];

export default config;
