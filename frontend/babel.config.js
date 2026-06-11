// babel.config.js
module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      // Add the missing plugin
      ['@babel/plugin-transform-nullish-coalescing-operator', { loose: true }],
      // Add optional chaining as well to be safe
      ['@babel/plugin-transform-optional-chaining', { loose: true }],
    ],
  };
};