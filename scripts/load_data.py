"""
Data loader script for importing aerodynamic data into the RAG vector store.

This script:
1. Downloads or loads the UIUC airfoil dataset
2. Parses airfoil data and metadata
3. Creates embeddings using OpenAI
4. Stores vectors in Chroma database

Usage:
    python scripts/load_data.py [--clear] [--csv-path /path/to/data.csv]
    
    Options:
        --clear: Clear existing data before loading (fresh start)
        --csv-path: Path to airfoil CSV file (defaults to data/uiuc_airfoils.csv)
"""
import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Generator

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import Settings, get_settings
from app.rag import RAGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Structures
# =============================================================================

class AirfoilData:
    """Container for airfoil metadata and characteristics."""
    
    def __init__(
        self,
        name: str,
        thickness_percent: float,
        camber_percent: float,
        max_cl: float,
        max_cd: float,
        description: str = ""
    ):
        """
        Initialize airfoil data.
        
        Args:
            name: Airfoil designation (e.g., "NACA 23012")
            thickness_percent: Max thickness as % of chord
            camber_percent: Max camber as % of chord
            max_cl: Maximum lift coefficient
            max_cd: Minimum drag coefficient
            description: Optional description
        """
        self.name = name
        self.thickness_percent = thickness_percent
        self.camber_percent = camber_percent
        self.max_cl = max_cl
        self.max_cd = max_cd
        self.description = description or self._generate_description()
    
    def _generate_description(self) -> str:
        """Generate a description from aerodynamic characteristics."""
        return (
            f"{self.name} airfoil with {self.thickness_percent:.1f}% thickness "
            f"and {self.camber_percent:.1f}% camber. "
            f"Characteristics: max CL {self.max_cl:.2f}, min CD {self.max_cd:.4f}. "
            f"Suitable for general aviation and racing applications."
        )
    
    def to_metadata(self) -> dict:
        """Convert to metadata dictionary for vector store."""
        return {
            "thickness_percent": self.thickness_percent,
            "camber_percent": self.camber_percent,
            "max_cl": self.max_cl,
            "max_cd": self.max_cd,
            "name": self.name
        }


# =============================================================================
# Data Loader
# =============================================================================

class AirfoilDataLoader:
    """
    Loads airfoil data from CSV file and populates RAG vector store.
    
    Expected CSV format:
        name,thickness_percent,camber_percent,max_cl,max_cd
        NACA 23012,11.6,2.5,1.45,0.0085
        ...
    """
    
    def __init__(self, rag_engine: RAGEngine, csv_path: Path):
        """
        Initialize data loader.
        
        Args:
            rag_engine: RAG engine instance for storing data
            csv_path: Path to airfoil CSV file
        """
        self.rag_engine = rag_engine
        self.csv_path = Path(csv_path)
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        
        logger.info(f"Data loader initialized with CSV: {self.csv_path}")
    
    def load_from_csv(self) -> Generator[AirfoilData, None, None]:
        """
        Load airfoil data from CSV file.
        
        Yields:
            AirfoilData: Parsed airfoil records
            
        Raises:
            ValueError: If CSV format is invalid
        """
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty or has no headers")
                
                required_fields = {
                    'name', 'thickness_percent', 'camber_percent',
                    'max_cl', 'max_cd'
                }
                missing_fields = required_fields - set(reader.fieldnames)
                if missing_fields:
                    raise ValueError(
                        f"CSV missing required fields: {missing_fields}\n"
                        f"Found: {reader.fieldnames}"
                    )
                
                for row_num, row in enumerate(reader, start=2):  # start=2 (after header)
                    try:
                        # Parse numeric fields
                        thickness = float(row['thickness_percent'])
                        camber = float(row['camber_percent'])
                        max_cl = float(row['max_cl'])
                        max_cd = float(row['max_cd'])
                        name = row['name'].strip()
                        
                        if not name:
                            logger.warning(f"Row {row_num}: Empty airfoil name, skipping")
                            continue
                        
                        yield AirfoilData(
                            name=name,
                            thickness_percent=thickness,
                            camber_percent=camber,
                            max_cl=max_cl,
                            max_cd=max_cd
                        )
                        
                    except ValueError as e:
                        logger.warning(f"Row {row_num}: Invalid numeric value, skipping: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise
    
    def populate_database(self, clear_first: bool = False) -> int:
        """
        Load all airfoils and populate RAG database.
        
        Args:
            clear_first: If True, clear existing data before loading
            
        Returns:
            int: Number of airfoils added
            
        Raises:
            Exception: If database operations fail
        """
        count = 0
        
        try:
            # Clear existing data if requested
            if clear_first:
                logger.info("Clearing existing data...")
                self.rag_engine.clear_collection()
            
            # Load and store airfoils
            logger.info("Loading airfoil data from CSV...")
            for airfoil in self.load_from_csv():
                document_id = f"airfoil_{airfoil.name.replace(' ', '_').lower()}"
                
                try:
                    self.rag_engine.add_airfoil(
                        airfoil_name=airfoil.name,
                        description=airfoil.description,
                        metadata=airfoil.to_metadata(),
                        document_id=document_id
                    )
                    count += 1
                    
                    if count % 50 == 0:
                        logger.info(f"Progress: {count} airfoils loaded...")
                
                except Exception as e:
                    logger.error(f"Failed to add airfoil {airfoil.name}: {e}")
                    continue
            
            logger.info(f"✓ Successfully loaded {count} airfoils into vector store")
            return count
        
        except Exception as e:
            logger.error(f"Database population failed: {e}")
            raise


# =============================================================================
# Command Line Interface
# =============================================================================

def main():
    """Entry point for data loading script."""
    parser = argparse.ArgumentParser(
        description="Load aerodynamic data into RAG vector store"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing data before loading"
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        help="Path to airfoil CSV file (default: data/uiuc_airfoils.csv)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load settings
        settings = get_settings()
        
        # Determine CSV path
        csv_path = args.csv_path or settings.airfoil_data_path
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            logger.info("\nPlease ensure you have the UIUC airfoil dataset.")
            logger.info("See README.md for instructions on downloading the data.")
            return 1
        
        # Initialize RAG engine
        logger.info("Initializing RAG engine...")
        rag_engine = RAGEngine(settings)
        
        # Create loader and populate database
        loader = AirfoilDataLoader(rag_engine, csv_path)
        count = loader.populate_database(clear_first=args.clear)
        
        logger.info("=" * 80)
        logger.info(f"Data loading complete: {count} airfoils stored")
        logger.info("=" * 80)
        return 0
    
    except KeyboardInterrupt:
        logger.info("\nData loading cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
