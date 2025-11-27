"""Data processing utilities for CSV, Excel, and other tabular data."""
import os
import json
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataProcessor:
    """Processes tabular data files (CSV, Excel, JSON)."""
    
    def __init__(self):
        self.temp_dir = "/tmp/data_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def load_csv(self, csv_path: str, **kwargs) -> Optional[pd.DataFrame]:
        """
        Load CSV file into DataFrame.
        
        Args:
            csv_path: Path to CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            DataFrame or None if failed
        """
        try:
            df = pd.read_csv(csv_path, **kwargs)
            logger.info(f"Loaded CSV: {csv_path}, Shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            # Try with different encodings
            for encoding in ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']:
                try:
                    df = pd.read_csv(csv_path, encoding=encoding, **kwargs)
                    logger.info(f"Loaded CSV with {encoding} encoding")
                    return df
                except:
                    continue
            return None
    
    def load_excel(self, excel_path: str, sheet_name: Any = 0) -> Optional[pd.DataFrame]:
        """
        Load Excel file into DataFrame.
        
        Args:
            excel_path: Path to Excel file
            sheet_name: Sheet name or index
            
        Returns:
            DataFrame or None if failed
        """
        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            logger.info(f"Loaded Excel: {excel_path}, Shape: {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error loading Excel: {e}")
            return None
    
    def load_json(self, json_path: str) -> Optional[Any]:
        """
        Load JSON file.
        
        Args:
            json_path: Path to JSON file
            
        Returns:
            Parsed JSON data or None if failed
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded JSON: {json_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON: {e}")
            return None
    
    def get_data_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get comprehensive information about a DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with data statistics
        """
        info = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
            "numeric_columns": list(df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": list(df.select_dtypes(include=['object', 'category']).columns),
            "datetime_columns": list(df.select_dtypes(include=['datetime64']).columns)
        }
        
        return info
    
    def get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get summary statistics for DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "describe": df.describe().to_dict(),
            "value_counts": {}
        }
        
        # Get value counts for categorical columns
        for col in df.select_dtypes(include=['object', 'category']).columns:
            if df[col].nunique() < 50:  # Only for columns with < 50 unique values
                stats["value_counts"][col] = df[col].value_counts().to_dict()
        
        return stats
    
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean column names (strip whitespace, lowercase, replace spaces).
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with cleaned column names
        """
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        logger.info("Cleaned column names")
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame, 
        strategy: str = 'drop'
    ) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.
        
        Args:
            df: Input DataFrame
            strategy: 'drop', 'fill_mean', 'fill_median', 'fill_mode', 'fill_zero'
            
        Returns:
            DataFrame with missing values handled
        """
        if strategy == 'drop':
            df = df.dropna()
        elif strategy == 'fill_mean':
            df = df.fillna(df.mean(numeric_only=True))
        elif strategy == 'fill_median':
            df = df.fillna(df.median(numeric_only=True))
        elif strategy == 'fill_mode':
            df = df.fillna(df.mode().iloc[0])
        elif strategy == 'fill_zero':
            df = df.fillna(0)
        
        logger.info(f"Handled missing values with strategy: {strategy}")
        return df
    
    def filter_dataframe(
        self, 
        df: pd.DataFrame, 
        column: str, 
        operator: str, 
        value: Any
    ) -> pd.DataFrame:
        """
        Filter DataFrame based on condition.
        
        Args:
            df: Input DataFrame
            column: Column name
            operator: Operator ('==', '!=', '>', '<', '>=', '<=', 'in', 'contains')
            value: Comparison value
            
        Returns:
            Filtered DataFrame
        """
        if operator == '==':
            result = df[df[column] == value]
        elif operator == '!=':
            result = df[df[column] != value]
        elif operator == '>':
            result = df[df[column] > value]
        elif operator == '<':
            result = df[df[column] < value]
        elif operator == '>=':
            result = df[df[column] >= value]
        elif operator == '<=':
            result = df[df[column] <= value]
        elif operator == 'in':
            result = df[df[column].isin(value)]
        elif operator == 'contains':
            result = df[df[column].str.contains(str(value), na=False)]
        else:
            logger.warning(f"Unknown operator: {operator}")
            result = df
        
        logger.info(f"Filtered from {len(df)} to {len(result)} rows")
        return result
    
    def aggregate_data(
        self, 
        df: pd.DataFrame, 
        group_by: List[str], 
        agg_dict: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Aggregate DataFrame.
        
        Args:
            df: Input DataFrame
            group_by: List of columns to group by
            agg_dict: Dictionary of {column: aggregation_function}
            
        Returns:
            Aggregated DataFrame
        """
        try:
            result = df.groupby(group_by).agg(agg_dict).reset_index()
            logger.info(f"Aggregated data: {result.shape}")
            return result
        except Exception as e:
            logger.error(f"Error aggregating data: {e}")
            return df
    
    def save_dataframe(self, df: pd.DataFrame, output_path: str, format: str = 'csv') -> str:
        """
        Save DataFrame to file.
        
        Args:
            df: DataFrame to save
            output_path: Output file path
            format: 'csv', 'excel', or 'json'
            
        Returns:
            Path to saved file
        """
        try:
            if format == 'csv':
                df.to_csv(output_path, index=False)
            elif format == 'excel':
                df.to_excel(output_path, index=False)
            elif format == 'json':
                df.to_json(output_path, orient='records')
            
            logger.info(f"Saved DataFrame to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error saving DataFrame: {e}")
            return ""
    
    def detect_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Detect and suggest appropriate data types for columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary of column: suggested_type
        """
        suggestions = {}
        
        for col in df.columns:
            # Try to convert to numeric
            try:
                pd.to_numeric(df[col])
                suggestions[col] = "numeric"
                continue
            except:
                pass
            
            # Try to convert to datetime
            try:
                pd.to_datetime(df[col])
                suggestions[col] = "datetime"
                continue
            except:
                pass
            
            # Check if it's categorical (low cardinality)
            if df[col].nunique() / len(df) < 0.5:
                suggestions[col] = "categorical"
            else:
                suggestions[col] = "text"
        
        return suggestions