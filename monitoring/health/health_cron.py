#!/usr/bin/env python3
"""
Cron Job para Health Checks
Ejecuta verificaciones de salud periódicamente y envía alertas
"""

import asyncio
import schedule
import time
import logging
import sys
import os
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from health_checker import HealthChecker, HealthStatus
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/health_cron.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthCheckScheduler:
    """Scheduler para health checks periódicos"""
    
    def __init__(self):
        self.last_healthy_status = True
        self.notification_cooldown = 300  # 5 minutos
        
    def send_notification(self, subject: str, body: str):
        """Enviar notificación por email (configurar según necesidades)"""
        try:
            # Configuración SMTP - personalizar según tu servidor
            smtp_server = os.getenv('SMTP_SERVER', 'localhost')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            from_email = os.getenv('FROM_EMAIL', 'alerts@ai-news.com')
            to_emails = os.getenv('TO_EMAILS', 'admin@ai-news.com').split(',')
            
            if not smtp_user or not smtp_password:
                logger.warning("Configuración SMTP no completa, usando logging local")
                logger.info(f"Notification - {subject}: {body}")
                return
            
            msg = MimeMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(from_email, to_emails, text)
            server.quit()
            
            logger.info(f"Email enviado: {subject}")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def run_health_check(self):
        """Ejecutar verificación de salud y evaluar cambios"""
        logger.info("=== Ejecutando Health Check Programado ===")
        
        async def check_and_notify():
            async with HealthChecker() as checker:
                results = await checker.run_all_checks()
                checker.log_summary()
                await checker.save_report(f"/var/log/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
                # Evaluar estado general
                critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
                current_status = critical_count == 0
                
                # Detectar cambios de estado
                if self.last_healthy_status != current_status:
                    if not current_status:
                        # Sistema pasó a estado crítico
                        subject = "🚨 ALERT: AI News System - Critical Issues Detected"
                        body = self.generate_alert_body(results, "CRITICAL ISSUES DETECTED")
                        self.send_notification(subject, body)
                        logger.critical("ALERT ENVIADO: Sistema en estado crítico")
                    else:
                        # Sistema se recuperó
                        subject = "✅ RECOVERED: AI News System - All Issues Resolved"
                        body = self.generate_alert_body(results, "ALL ISSUES RESOLVED")
                        self.send_notification(subject, body)
                        logger.info("ALERT ENVIADO: Sistema recuperado")
                    
                    self.last_healthy_status = current_status
                
                # Verificar si hay problemas críticos (sin cambio de estado)
                elif critical_count > 0:
                    critical_components = [r.component for r in results if r.status == HealthStatus.CRITICAL]
                    logger.warning(f"Problemas críticos detectados: {critical_components}")
        
        # Ejecutar el check asíncrono
        asyncio.run(check_and_notify())
    
    def generate_alert_body(self, results, title):
        """Generar cuerpo HTML para alertas"""
        critical = [r for r in results if r.status == HealthStatus.CRITICAL]
        warning = [r for r in results if r.status == HealthStatus.WARNING]
        healthy = [r for r in results if r.status == HealthStatus.HEALTHY]
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .section {{ margin: 20px 0; }}
                .critical {{ background-color: #ffebee; border-left: 4px solid #f44336; padding: 10px; }}
                .warning {{ background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; }}
                .healthy {{ background-color: #e8f5e8; border-left: 4px solid #4caf50; padding: 10px; }}
                .timestamp {{ color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>AI News Aggregator System Status Report</p>
                <p class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <ul>
                    <li><strong>Total Checks:</strong> {len(results)}</li>
                    <li><strong>Healthy:</strong> {len(healthy)}</li>
                    <li><strong>Warnings:</strong> {len(warning)}</li>
                    <li><strong>Critical:</strong> {len(critical)}</li>
                </ul>
            </div>
        """
        
        if critical:
            html += """
            <div class="section">
                <h2>Critical Issues</h2>
            """
            for result in critical:
                html += f"""
                <div class="critical">
                    <h3>{result.component}</h3>
                    <p><strong>Status:</strong> {result.status.value}</p>
                    <p><strong>Message:</strong> {result.message}</p>
                    <p><strong>Response Time:</strong> {result.response_time}s</p>
                </div>
                """
            html += "</div>"
        
        if warning:
            html += """
            <div class="section">
                <h2>Warnings</h2>
            """
            for result in warning:
                html += f"""
                <div class="warning">
                    <h3>{result.component}</h3>
                    <p><strong>Status:</strong> {result.status.value}</p>
                    <p><strong>Message:</strong> {result.message}</p>
                    <p><strong>Response Time:</strong> {result.response_time}s</p>
                </div>
                """
            html += "</div>"
        
        html += """
            <div class="section">
                <h2>Monitoring Links</h2>
                <ul>
                    <li><a href="http://localhost:9090">Prometheus</a></li>
                    <li><a href="http://localhost:3000">Grafana</a></li>
                    <li><a href="http://localhost:9093">AlertManager</a></li>
                    <li><a href="http://localhost:5601">Kibana (Logs)</a></li>
                    <li><a href="http://localhost:3001">Uptime Kuma</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def start(self):
        """Iniciar scheduler"""
        logger.info("Iniciando Health Check Scheduler")
        
        # Programar verificaciones
        schedule.every(5).minutes.do(self.run_health_check)  # Cada 5 minutos
        schedule.every(1).hours.do(self.run_health_check)    # Cada hora
        schedule.every().day.at("02:00").do(self.run_health_check)  # Limpieza diaria a las 2 AM
        
        # Ejecutar primera verificación inmediatamente
        self.run_health_check()
        
        # Loop principal
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto

def main():
    """Función principal"""
    try:
        scheduler = HealthCheckScheduler()
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Health Check Scheduler detenido por usuario")
    except Exception as e:
        logger.error(f"Error en Health Check Scheduler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()