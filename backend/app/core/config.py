import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv не обов'язковий
    pass


# Singleton
class Settings:
    _instance: "Settings | None" = None

    def __new__(cls) -> "Settings":
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._load()
            cls._instance = instance
        return cls._instance

    def _load(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://food:food@localhost:3306/food_delivery?charset=utf8mb4",
        )
        self.jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
        self.jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]
        self.seed_demo_data: bool = os.getenv("SEED_DEMO_DATA", "1") == "1"
        # Імітація роботи ресторану та кур'єра
        self.simulation_enabled: bool = os.getenv("SIMULATION_ENABLED", "1") == "1"
        self.sim_step_seconds: int = int(os.getenv("SIM_STEP_SECONDS", "20"))
        self.sim_delivery_seconds: int = int(os.getenv("SIM_DELIVERY_SECONDS", "90"))


def get_settings() -> Settings:
    return Settings()
