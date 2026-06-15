const path = require('path');
const webpack = require('webpack');
const WebpackDashDynamicImport = require('@plotly/webpack-dash-dynamic-import');
const packagejson = require('./package.json');

const dashLibraryName = packagejson.name.replace(/-/g, '_');

module.exports = (env, argv) => {
    const mode = (argv && argv.mode) || 'production';
    const modeSuffix = mode === 'development' ? 'dev' : 'min';

    return {
        mode,
        entry: {main: './src/lib/index.js'},
        output: {
            path: path.resolve(__dirname, dashLibraryName),
            chunkFilename: '[name].js',
            filename: `${dashLibraryName}.${modeSuffix}.js`,
            library: dashLibraryName,
            libraryTarget: 'window',
        },
        // Source maps are emitted by SourceMapDevToolPlugin below; setting
        // devtool here as well would emit a second, conflicting map file.
        devtool: false,
        externals: {
            react: 'React',
            'react-dom': 'ReactDOM',
            'prop-types': 'PropTypes',
        },
        module: {
            rules: [
                {
                    test: /\.jsx?$/,
                    exclude: /node_modules/,
                    use: {loader: 'babel-loader'},
                },
                {
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'],
                },
            ],
        },
        optimization: {
            splitChunks: {
                name: '[name].js',
                cacheGroups: {
                    async: {
                        chunks: 'async',
                        minSize: 0,
                        name(module, chunks, cacheGroupKey) {
                            return `${cacheGroupKey}-${chunks[0].name}`;
                        },
                    },
                    shared: {
                        chunks: 'all',
                        minSize: 0,
                        minChunks: 2,
                        name: `${dashLibraryName}-shared`,
                    },
                },
            },
        },
        plugins: [
            new WebpackDashDynamicImport(),
            new webpack.SourceMapDevToolPlugin({
                filename: '[file].map',
            }),
        ],
    };
};
