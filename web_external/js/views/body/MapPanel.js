minerva.views.MapPanel = minerva.View.extend({

    events: {
        'click .m-save-current-baselayer': function () {
            this.session.sessionJsonContents.center = this.map.center();
            this.session.sessionJsonContents.zoom = this.map.zoom();
            this.session.saveSession();
        }
    },

    _specifyWmsDatasetLayer: function (dataset, layer) {
        var minervaMetadata = dataset.getMinervaMetadata();
        var baseUrl = minervaMetadata.base_url;
        var layerName = minervaMetadata.type_name;
        // TODO: inclued projection in params ??
        var projection = 'EPSG:3857';
        layer.gcs(projection);
        layer.tileUrl(
            function (zoom, x, y) {
                var xLowerLeft = geo.mercator.tilex2long(x, zoom);
                var yLowerLeft = geo.mercator.tiley2lat(y + 1, zoom);
                var xUpperRight = geo.mercator.tilex2long(x + 1, zoom);
                var yUpperRight = geo.mercator.tiley2lat(y, zoom);

                var sw = geo.mercator.ll2m(xLowerLeft, yLowerLeft, true);
                var ne = geo.mercator.ll2m(xUpperRight, yUpperRight, true);
                var bbox_mercator = sw.x + ',' + sw.y + ',' + ne.x + ',' + ne.y;
                var params = {
                    SERVICE: 'WMS',
                    VERSION: '1.3.0',
                    REQUEST: 'GetMap',
                    LAYERS: layerName,
                    STYLES: '',
                    BBOX: bbox_mercator,
                    WIDTH: 256,
                    HEIGHT: 256,
                    FORMAT: 'image/png',
                    TRANSPARENT: true,
                    SRS: projection,
                    TILED: true
                };
                return baseUrl + '?' + $.param(params);
            }
        );
    },

    addDataset: function (dataset) {
        // TODO HACK
        // deleting and re-adding ui layer to keep it on top
        //this.map.deleteLayer(this.uiLayer);
        // this causes a problem when there are at least two feature layers,
        // so for now it is commented out
        // this means we keep re-adding the ui layer each time a dataset is
        // added as a feature layer, which is even more of a HACK
        if (!_.contains(this.datasetLayers, dataset.id)) {
            if (dataset.getDatasetType() === 'wms') {
                var datasetId = dataset.id;
                var layer = this.map.createLayer('osm');
                this.datasetLayers[datasetId] = layer;
                this._specifyWmsDatasetLayer(dataset, layer);

                this.legendWidget[datasetId] = new minerva.views.LegendWidget({
                    el: $('.m-map-legend-container'),
                    parentView: this,
                    id: datasetId,
                    legend: 'data:image/png;base64,' + dataset.getMinervaMetadata().legend
                });
                this.legendWidget[datasetId].render();
                this.legendWidget[datasetId].show();

                // Add the UI slider back
                this.uiLayer = this.map.createLayer('ui');
                this.uiLayer.createWidget('slider');
                this.map.draw();
            } else {
                // Assume the dataset provides a reader, so load the data
                // and adapt the dataset to the map with the reader.
                dataset.once('m:dataLoaded', function (datasetId) {
                    // TODO: allow these datasets to specify a legend.
                    var dataset = this.collection.get(datasetId);
                    var layer = this.map.createLayer('feature');

                    var reader = geo.createFileReader(dataset.geoFileReader, {layer: layer});
                    this.datasetLayers[datasetId] = layer;

                    layer.clear();

                    reader.read(dataset.fileData, _.bind(function () {
                        // Add the UI slider back
                        this.uiLayer = this.map.createLayer('ui');
                        this.uiLayer.createWidget('slider');
                        this.map.draw();
                    }, this));
                }, this);

                dataset.loadData();
            }
        }
    },

    removeDataset: function (dataset) {
        var datasetId = dataset.id;
        var layer = this.datasetLayers[datasetId];
        if (_.has(this.legendWidget, datasetId)) {
            this.legendWidget[datasetId].remove(datasetId);
            delete this.legendWidget[datasetId];
        }
        if (dataset.getDatasetType() === 'wms' && layer) {
            this.map.deleteLayer(layer);
        } else if (layer) {
            layer.clear();
            layer.draw();
        }
        delete this.datasetLayers[datasetId];
    },

    initialize: function (settings) {
        this.session = settings.session;
        this.listenTo(this.session, 'm:mapUpdated', function () {
            // TODO for now only dealing with center
            if (this.map) {
                // TODO could better separate geojs needs from session storage
                this.map.center(this.session.sessionJsonContents.center);
            }
        });
        this.datasetLayers = {};
        this.legendWidget = {};

        this.collection = settings.collection;
        this.listenTo(this.collection, 'change:displayed', function (dataset) {
            // There is a slight danger of a user trying to add a dataset
            // to a session while the map is not yet created.  If the map isn't
            // created, we don't need to add/remove the datasets here because
            // they will be taken care of in the renderMap initialization block.
            if (this.mapCreated) {
                if (dataset.get('displayed')) {
                    this.addDataset(dataset);
                } else {
                    this.removeDataset(dataset);
                }
            }
        }, this);
    },

    renderMap: function () {
        if (!this.map) {
            this.map = geo.map({
                node: '.mapPanelMap',
                center: this.session.sessionJsonContents.center,
                zoom: this.session.sessionJsonContents.zoom
            });
            this.map.createLayer(this.session.sessionJsonContents.basemap);
            this.uiLayer = this.map.createLayer('ui');
            this.uiLayer.createWidget('slider');
            this.mapCreated = true;
            _.each(this.collection.models, function (dataset) {
                if (dataset.get('displayed')) {
                    this.addDataset(dataset);
                }
            }, this);
        }
        this.map.draw();
    },

    render: function () {
        this.$el.html(minerva.templates.mapPanel({}));
        this.renderMap();
        var tooltipProperties = {
            placement: 'left',
            delay: 400,
            container: this.$el,
            trigger: 'hover'
        };
        this.$('.m-save-current-baselayer').tooltip(tooltipProperties);
        return this;
    }
});
