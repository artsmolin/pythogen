from dataclasses import dataclass
from typing import Any
from typing import Dict


@dataclass
class ResolvedRef:
    ref_data: Any
    ref_id: str


class RefResolver:
    """
    Отвечает за получение данных из указанного $ref пути.
    """

    def __init__(self, openapi_data: Dict[str, Any]) -> None:
        self._openapi_data = openapi_data

    def resolve(self, ref: str) -> ResolvedRef:
        """
        Получить данные из указзаного $ref-пути

        Parameters
        ----------
        ref
            Путь до объекта. Пример: "#/components/schemas/PutObjectData"
        """
        _, path = ref.split('#/')
        segments = path.split('/')
        target = self._openapi_data
        while segments:
            current = segments.pop(0)
            if current not in target:
                raise Exception(f'Unable to resolve "{ref}", document section "{current}" not found')
            target = target[current]
        return ResolvedRef(ref_data=target, ref_id=ref.split('/')[-1])
