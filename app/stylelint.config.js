const KEBAB = "[a-z][a-z0-9]*(?:-[a-z0-9]+)*";
const BEM_CLASS = new RegExp(`^${KEBAB}(?:__${KEBAB})?(?:--${KEBAB})?$`);

export default {
  extends: ["stylelint-config-standard"],
  rules: {
    "selector-class-pattern": [
      BEM_CLASS,
      { message: "Expected class to be BEM: block__element--modifier" },
    ],
  },
};
