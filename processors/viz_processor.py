"""Visualization generation utilities."""
import os
import base64
from typing import Optional, Dict, Any, List
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VizProcessor:
    """Creates visualizations and charts."""
    
    def __init__(self):
        self.temp_dir = "/tmp/viz_processing"
        os.makedirs(self.temp_dir, exist_ok=True)
        sns.set_style("whitegrid")
    
    def create_bar_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "Bar Chart",
        output_path: Optional[str] = None
    ) -> str:
        """Create a bar chart using matplotlib."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(data[x_col], data[y_col])
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(title)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "bar_chart.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created bar chart: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating bar chart: {e}")
            return ""
    
    def create_line_chart(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        title: str = "Line Chart",
        output_path: Optional[str] = None
    ) -> str:
        """Create a line chart."""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for y_col in y_cols:
                ax.plot(data[x_col], data[y_col], marker='o', label=y_col)
            
            ax.set_xlabel(x_col)
            ax.set_ylabel("Value")
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "line_chart.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created line chart: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating line chart: {e}")
            return ""
    
    def create_scatter_plot(
        self,
        data: pd.DataFrame,
        x_col: str,
        y_col: str,
        title: str = "Scatter Plot",
        output_path: Optional[str] = None
    ) -> str:
        """Create a scatter plot."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(data[x_col], data[y_col], alpha=0.6)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(title)
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "scatter_plot.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created scatter plot: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating scatter plot: {e}")
            return ""
    
    def create_histogram(
        self,
        data: pd.DataFrame,
        column: str,
        bins: int = 30,
        title: str = "Histogram",
        output_path: Optional[str] = None
    ) -> str:
        """Create a histogram."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.hist(data[column].dropna(), bins=bins, edgecolor='black', alpha=0.7)
            ax.set_xlabel(column)
            ax.set_ylabel("Frequency")
            ax.set_title(title)
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "histogram.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created histogram: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating histogram: {e}")
            return ""
    
    def create_heatmap(
        self,
        data: pd.DataFrame,
        title: str = "Heatmap",
        output_path: Optional[str] = None
    ) -> str:
        """Create a correlation heatmap."""
        try:
            # Select only numeric columns
            numeric_data = data.select_dtypes(include=['number'])
            correlation = numeric_data.corr()
            
            fig, ax = plt.subplots(figsize=(12, 10))
            sns.heatmap(correlation, annot=True, fmt='.2f', cmap='coolwarm', 
                       center=0, ax=ax, square=True)
            ax.set_title(title)
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "heatmap.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created heatmap: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating heatmap: {e}")
            return ""
    
    def create_pie_chart(
        self,
        data: pd.DataFrame,
        column: str,
        title: str = "Pie Chart",
        output_path: Optional[str] = None
    ) -> str:
        """Create a pie chart."""
        try:
            value_counts = data[column].value_counts()
            
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%',
                  startangle=90)
            ax.set_title(title)
            plt.tight_layout()
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "pie_chart.png")
            
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Created pie chart: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating pie chart: {e}")
            return ""
    
    def create_interactive_plotly(
        self,
        data: pd.DataFrame,
        chart_type: str,
        x_col: str,
        y_col: str,
        title: str = "Interactive Chart",
        output_path: Optional[str] = None
    ) -> str:
        """Create an interactive Plotly chart and save as HTML."""
        try:
            if chart_type == "scatter":
                fig = px.scatter(data, x=x_col, y=y_col, title=title)
            elif chart_type == "line":
                fig = px.line(data, x=x_col, y=y_col, title=title)
            elif chart_type == "bar":
                fig = px.bar(data, x=x_col, y=y_col, title=title)
            else:
                fig = px.scatter(data, x=x_col, y=y_col, title=title)
            
            if output_path is None:
                output_path = os.path.join(self.temp_dir, "interactive_chart.html")
            
            fig.write_html(output_path)
            logger.info(f"Created interactive Plotly chart: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creating Plotly chart: {e}")
            return ""
    
    def encode_image_base64(self, image_path: str) -> str:
        """Encode image to base64 data URI."""
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            base64_str = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/png;base64,{base64_str}"
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return ""