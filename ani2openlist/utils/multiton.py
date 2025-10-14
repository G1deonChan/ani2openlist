import abc


class Multiton(abc.ABCMeta, type):
    """
    多例模式
    """

    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        key = (cls, args, frozenset(kwargs.items()))
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]
    
    @classmethod
    def clear_instances(mcs):
        """
        清除所有缓存的实例
        用于资源清理，防止复用已关闭资源的实例
        """
        mcs._instances.clear()
