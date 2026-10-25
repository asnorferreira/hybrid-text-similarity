import torch
from torch import nn
import torch.nn.functional as F


def pool_tensors(embeddings, counts):
    if not embeddings or len(embeddings) != len(counts) or any(type(c) is not int or c <= 0 for c in counts):
        raise ValueError('nonempty windows with positive content counts required')
    stacked = torch.stack(embeddings)
    weights = stacked.new_tensor(counts)
    return F.normalize((stacked*weights[:,None]).sum(0)/weights.sum(), dim=0)


class WindowEncoder(nn.Module):
    def __init__(self, model, tokenizer, limit):
        super().__init__()
        self.model, self.tokenizer, self.limit = model, tokenizer, limit
        self.capacity = limit-tokenizer.num_special_tokens_to_add(pair=False)
        if self.capacity < 1:
            raise ValueError('no room for content')
        self.diagnostics = []

    def forward(self, text):
        encoded = self.tokenizer(text, add_special_tokens=False, truncation=False).encodings[0]
        original = list(encoded.ids)
        if not original or len(original) > 12000:
            raise ValueError('empty or oversized token input')
        encoded.truncate(self.capacity, stride=0)
        chunks = [encoded, *encoded.overflowing]
        if [x for chunk in chunks for x in chunk.ids] != original:
            raise ValueError('incomplete token coverage')
        embeddings, counts = [], []
        for chunk in chunks:
            prepared = self.tokenizer.backend_tokenizer.post_process(chunk, add_special_tokens=True)
            if len(prepared.ids) > self.limit:
                raise ValueError('window exceeds model limit')
            features = {k:torch.tensor([v], dtype=torch.long) for k,v in (
                ('input_ids',prepared.ids), ('attention_mask',prepared.attention_mask), ('token_type_ids',prepared.type_ids))}
            embeddings.append(self.model(features)['sentence_embedding'][0])
            counts.append(len(chunk.ids))
        self.diagnostics.append({'tokens':len(original), 'window_tokens':counts, 'covered':sum(counts)})
        return pool_tensors(embeddings, counts)


class Siamese(nn.Module):
    def __init__(self, encoder, dimension=384, hidden=128, dropout=.1, alpha=.1, epsilon=1e-5, train_encoder=True):
        super().__init__()
        self.encoder = encoder
        for parameter in encoder.parameters():
            parameter.requires_grad_(train_encoder)
        self.head = nn.Sequential(nn.Linear(2*dimension, hidden), nn.LayerNorm(hidden,eps=epsilon),
                                  nn.LeakyReLU(alpha), nn.Dropout(dropout), nn.Linear(hidden,1), nn.Sigmoid())

    def forward(self, source_text, suspect_text):
        u, v = self.encoder(source_text), self.encoder(suspect_text)
        return self.head(torch.cat((torch.abs(u-v),u*v))).reshape(())


def load_local_trainable(config):
    from hts_core.adapters.semantic import SemanticEncoder
    adapter = SemanticEncoder()
    encoder = WindowEncoder(adapter.model, adapter.tokenizer, adapter.limit)
    spec = config['siamese']
    return Siamese(encoder, spec['embedding_dimension'], spec['dense_dimensions'][1], spec['dropout'],
                   spec['leaky_relu_alpha'], spec['layer_norm_epsilon'], spec['encoder_trainable']), adapter.identity
