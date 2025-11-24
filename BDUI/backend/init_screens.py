"""
Модуль для автоматической инициализации экранов при первом запуске
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from models import Screen
from database import SessionLocal

def init_screens_from_json():
    """
    Загружает экраны из JSON файлов, если база данных пустая
    Запускается автоматически при старте backend
    """
    db = SessionLocal()
    
    try:
        existing_count = db.query(Screen).count()
        
        if existing_count > 0:
            print(f"✅ В базе уже есть {existing_count} экран(ов). Инициализация не требуется.")
            return True
        
        print("🔄 База данных пустая. Загружаем экраны из JSON файлов...")
        
        base_dir = Path(__file__).parent.parent
        screens_dir = base_dir / "screens"
        
        if not screens_dir.exists():
            print(f"⚠️  Директория screens/ не найдена: {screens_dir}")
            return False
        
        screen_files = [
            "home_screen.json",
            "home_2_screen.json",
            "home_3_screen.json",
            "avito_catalog_screen.json"
        ]
        
        success_count = 0
        
        for filename in screen_files:
            filepath = screens_dir / filename
            
            if not filepath.exists():
                print(f"⚠️  Файл не найден: {filename}")
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                screen_name = data.get('name')
                if not screen_name:
                    print(f"⚠️  Некорректный JSON в {filename}: отсутствует 'name'")
                    continue
                
                screen = Screen(
                    name=screen_name,
                    title=data.get('title', ''),
                    description=data.get('description', ''),
                    config=data.get('config', {}),
                    platform=data.get('platform', 'mobile'),
                    locale=data.get('locale', 'ru'),
                    is_active=data.get('is_active', True)
                )
                
                db.add(screen)
                db.commit()
                
                print(f"✅ Загружен: {screen_name}")
                success_count += 1
                
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON в {filename}: {e}")
            except Exception as e:
                print(f"❌ Ошибка при обработке {filename}: {e}")
                db.rollback()
        
        if success_count > 0:
            print(f"🎉 Успешно загружено {success_count} экран(ов)!")
            return True
        else:
            print("⚠️  Не удалось загрузить ни одного экрана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации экранов: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    init_screens_from_json()

