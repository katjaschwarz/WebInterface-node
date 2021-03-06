import os
import numpy as np
import pandas as pd
import deepdish as dd
import torch
from umap import UMAP


from .communication import make_nodes
from .train import initialize_embedder, compute_embedding
from .model import MapNet


info_file = '/export/home/kschwarz/Documents/Masters/WebInterface/MapNetCode/pretraining/wikiart_datasets/info_elgammal_subset_test.hdf5'
# feature_file = '/export/home/kschwarz/Documents/Masters/WebInterface/MapNetCode/features/NarrowNet128_MobileNetV2_info_artist_49_multilabel_test.hdf5'
feature_file = '/export/home/kschwarz/Documents/Masters/WebInterface/MapNetCode/evaluation/pretrained_features/NarrowNet512_MobileNetV2_info_elgammal_subset_test_genre.hdf5'
weight_file = None#'runs/embedder/models/TEST_MapNet_embedder.pth.tar'

info_file_shape = '/export/home/kschwarz/Documents/Data/Geometric_Shapes/labels.hdf5'
feature_file_shape = 'features/ShapeDataset_NarrowNet128_MobileNetV2_test.hdf5'
weight_file_shape = 'runs/embedder/models/ShapeDataset_TEST_MapNet_embedder.pth.tar'#None#'runs/embedder/models/ShapeDataset_MapNet_embedder_09-12-13-07.pth.tar'

info_file_office = '/export/home/kschwarz/Documents/Data/OfficeHomeDataset_10072016/info_test.hdf5'
feature_file_office = 'features/OfficeDataset_NarrowNet128_MobileNetV2_info_test.hdf5'
weight_file_office = None#'runs/embedder/models/ShapeDataset_TEST_MapNet_embedder.pth.tar'#None#'runs/embedder/models/ShapeDataset_MapNet_embedder_09-12-13-07.pth.tar'

info_file_bam = '/export/home/kschwarz/Documents/Data/BAM/info_test.hdf5'
feature_file_bam = 'features/BAMDataset_NarrowNet128_MobileNetV2_info_test.hdf5'
weight_file_bam = 'runs/embedder/models/BAMDatasetTEST_MapNet_embedder.pth.tar'

# if not os.getcwd().endswith('/MapNetCode'):
#     os.chdir(os.path.join(os.getcwd(), 'MapNetCode'))


def load_feature(feature_file):
    """Load features from feature file."""
    if not os.path.isfile(feature_file):
        raise RuntimeError('Feature file not found.')

    data = dd.io.load(feature_file)
    try:
        name, feature = data['image_names'], data['features']
    except KeyError:
        name, feature = data['image_name'], data['features']

    return name, feature


def initialize(dataset='wikiart', **kwargs):   #(info_file, feature_file, weight_file=None):
    print(os.getcwd())
    if 'experiment_id' not in kwargs.keys():
        kwargs['experiment_id'] = None
    if dataset == 'shape':
        if kwargs['experiment_id'] is None or 'ShapeDataset' in kwargs['experiment_id']:
            kwargs['experiment_id'] = 'ShapeDataset'
        else:
            kwargs['experiment_id'] = 'ShapeDataset_' + kwargs['experiment_id']

        data = dd.io.load(info_file_shape)['df']
        split = feature_file_shape.split('_')[-1].replace('.hdf5', '')
        print('Shape Dataset Split: {}'.format(split))
        if split == 'train':
            split = 0
        elif split == 'val':
            split = 1
        else:       # test
            split = 2
        data = data.loc[data['split'] == split]
        data.index = range(len(data))

        id = data['image_id']
        categories = sorted(['shape', 'n_shapes', 'color_shape', 'color_background'])
        ft_id, feature = load_feature(feature_file_shape)

    elif dataset == 'office':
        if kwargs['experiment_id'] is None or 'OfficeDataset' in kwargs['experiment_id']:
            kwargs['experiment_id'] = 'OfficeDataset'
        else:
            kwargs['experiment_id'] = 'OfficeDataset' + kwargs['experiment_id']
        data = dd.io.load(info_file_office)['df']
        id = data['image_id']
        categories = sorted(['style', 'genre'])
        ft_id, feature = load_feature(feature_file_office)

    elif dataset == 'bam':
        if kwargs['experiment_id'] is None or 'BAMDataset' in kwargs['experiment_id']:
            kwargs['experiment_id'] = 'BAMDataset'
        else:
            kwargs['experiment_id'] = 'BAMDataset' + kwargs['experiment_id']
        data = dd.io.load(info_file_bam)['df']
        id = data['image_id']
        categories = sorted(['content', 'emotion', 'media'])
        ft_id, feature = load_feature(feature_file_bam)
    elif dataset == 'wikiart_elgammal':
        data = dd.io.load(info_file)['df']
        valid_idcs = data[['artist_name', 'genre']].dropna().index
        data = data.loc[valid_idcs]
        data.index = range(len(data))
        id = data['image_id']
        data['style'][data['style'].isnull()] = None
        data['media'][data['media'].isnull()] = None
        data['century'][data['century'].isnull()] = None
        categories = sorted(['artist_name', 'genre'])#''style', 'genre', 'media', 'century'])
        ft_id, feature = load_feature(feature_file)
        ft_id = ft_id[valid_idcs]
        feature = feature[valid_idcs]
    else:
        data = dd.io.load(info_file)['df']
        id = data['image_id']

        categories = sorted(['artist_name', 'style', 'genre', 'technique', 'century'])
        ft_id, feature = load_feature(feature_file)

    label = np.stack([data[k] for k in sorted(data.keys()) if k in categories], axis=1)
    label = np.concatenate([label, np.full((len(label), 1), None)], axis=1)
    categories.append('group')

    if not (ft_id == id).all():
        raise ValueError('Image IDs in feature file do not match IDs in info file.')
    del ft_id

    # # initialize the network
    net = MapNet(feature_dim=feature.shape[1], output_dim=2)
    # if dataset == 'shape':
    #     initialize_embedder(net.embedder, weight_file_shape, feature, **kwargs)
    # elif dataset == 'office':
    #     initialize_embedder(net.embedder, weight_file_office, feature, **kwargs)
    # elif dataset == 'bam':
    #     initialize_embedder(net.embedder, weight_file_bam, feature, **kwargs)
    # else:
    #     initialize_embedder(net.embedder, weight_file, feature, **kwargs)
    # embedding = compute_embedding(net.embedder, feature)
    # compute umap embedding
    proj_path = 'projections'
    if not os.path.isdir(proj_path):
        os.makedirs(proj_path)
    proj_file = os.path.join(proj_path, feature_file.split('/')[-1].replace('.hdf5', '_minspace.npy'))
    if not os.path.isfile(proj_file):
        projector = UMAP(n_neighbors=30, min_dist=0.25)
        embedding = projector.fit_transform(feature)
        np.save(proj_file, embedding)
    else:
        embedding = np.load(proj_file)

    data = {
        'name': id,
        'label': label,
        'position': embedding,
        'feature': feature,
        'categories': categories,
        'experiment_id': kwargs['experiment_id']
    }

    print('Prepare network for training...')
    # add a tiny bit of noise, so each parameter in mapping contributes (otherwise gradients are way too small)
    for name, param in net.mapping.named_parameters():
        if name.endswith('weight'):
            param.data.copy_(param.data + torch.rand(param.shape).type_as(param.data) * 1e-8)
    print('Done.')

    return net, data
