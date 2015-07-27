from clld.web.maps import ParameterMap, CombinationMap


class FeatureMap(ParameterMap):
    def get_options(self):
        return {
            'icon_size': 20,
            'max_zoom': 9,
            'worldCopyJump': True,
            'info_query': {'parameter': self.ctx.pk}}


class CombinedMap(CombinationMap):
    def get_options(self):
        return {'icon_size': 20, 'hash': True}


def includeme(config):
    config.register_map('parameter', FeatureMap)
