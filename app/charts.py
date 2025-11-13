import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64
import traceback
from utils.logger import setup_logger

logger = setup_logger()

def generate_charts(metrics_list):
    """Generate matplotlib charts from metrics data."""
    try:
        logger.info(f"Generating charts from {len(metrics_list)} metrics...")
        
        if not metrics_list or len(metrics_list) < 2:
            logger.info("✓ Not enough data for charts (need at least 2 points)")
            return {}
        
        charts = {}
        
        # CPU Chart
        cpu_data = [m.get('cpu_percent', 0) for m in metrics_list if m.get('cpu_percent') is not None]
        if cpu_data and len(cpu_data) > 1:
            logger.info("Generating CPU chart...")
            cpu_timestamps = [m.get('timestamp', '')[-8:] for m in metrics_list if m.get('cpu_percent') is not None]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(cpu_timestamps, cpu_data, marker='o', linewidth=2, markersize=4, color='#667eea')
            ax.set_xlabel('Time')
            ax.set_ylabel('CPU Usage (%)')
            ax.set_title('CPU Usage Over Time')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            charts['CPU Usage'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            logger.info("✓ CPU chart generated")
        
        # RAM Chart
        ram_data = [m.get('ram', {}).get('percent', 0) for m in metrics_list if m.get('ram', {}).get('percent') is not None]
        if ram_data and len(ram_data) > 1:
            logger.info("Generating RAM chart...")
            ram_timestamps = [m.get('timestamp', '')[-8:] for m in metrics_list if m.get('ram', {}).get('percent') is not None]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(ram_timestamps, ram_data, marker='o', linewidth=2, markersize=4, color='#764ba2')
            ax.set_xlabel('Time')
            ax.set_ylabel('RAM Usage (%)')
            ax.set_title('RAM Usage Over Time')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            charts['RAM Usage'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            logger.info("✓ RAM chart generated")
        
        # GPU Chart
        gpu_data = [m.get('gpu_percent') for m in metrics_list if m.get('gpu_percent') is not None]
        if gpu_data and len(gpu_data) > 1:
            logger.info("Generating GPU chart...")
            gpu_timestamps = [m.get('timestamp', '')[-8:] for m in metrics_list if m.get('gpu_percent') is not None]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(gpu_timestamps, gpu_data, marker='o', linewidth=2, markersize=4, color='#22c55e')
            ax.set_xlabel('Time')
            ax.set_ylabel('GPU Usage (%)')
            ax.set_title('GPU Usage Over Time')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            charts['GPU Usage'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            logger.info("✓ GPU chart generated")
        
        # Ping Chart
        ping_data = [m.get('ping_ms') for m in metrics_list if m.get('ping_ms') is not None]
        if ping_data and len(ping_data) > 1:
            logger.info("Generating Ping chart...")
            ping_timestamps = [m.get('timestamp', '')[-8:] for m in metrics_list if m.get('ping_ms') is not None]
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(ping_timestamps, ping_data, marker='o', linewidth=2, markersize=4, color='#f59e0b')
            ax.set_xlabel('Time')
            ax.set_ylabel('Ping (ms)')
            ax.set_title('Network Latency Over Time')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            charts['Network Latency'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
            logger.info("✓ Ping chart generated")
        
        logger.info(f"✓ Generated {len(charts)} charts total")
        return charts
    except Exception as e:
        logger.error(f"✗ Chart generation failed: {str(e)}")
        logger.error(traceback.format_exc())
        return {}