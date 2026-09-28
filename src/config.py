"""Configuración central del simulador de seguimiento."""

ACTION_LABELS = {
    0: "Sin contacto",
    1: "Mensaje",
    2: "Llamada",
    3: "Teleorientación",
}

DEFAULT_ACTION_COSTS = {
    0: 0,
    1: 1,
    2: 3,
    3: 5,
}

DEFAULT_MONTHLY_CAPACITY = 100
