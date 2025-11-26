"""
Скрипт для принудительной загрузки экранов из JSON файлов
Использование: python load_screens_from_json.py
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from models import Screen
from database import SessionLocal

def load_screens_from_json():
    """
    Принудительно загружает экраны из JSON файлов
    Обновляет существующие или создает новые
    """
    db = SessionLocal()
    
    try:
        print("🔄 Загружаем экраны из JSON файлов...")
        
        screens_dir = Path("/screens")
        
        if not screens_dir.exists():
            print(f"⚠️  Директория screens/ не найдена: {screens_dir}")
            return False
        
        screen_files = list(screens_dir.glob("*.json"))
        
        if not screen_files:
            print("⚠️  JSON файлы не найдены в папке screens/")
            return False
        
        success_count = 0
        
        for filepath in screen_files:
            filename = filepath.name
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                screen_name = data.get('name')
                if not screen_name:
                    print(f"⚠️  Некорректный JSON в {filename}: отсутствует 'name'")
                    continue
                
                existing_screen = db.query(Screen).filter(Screen.name == screen_name).first()
                
                if existing_screen:
                    existing_screen.title = data.get('title', existing_screen.title)
                    existing_screen.description = data.get('description', existing_screen.description)
                    existing_screen.config = data.get('config', existing_screen.config)
                    existing_screen.platform = data.get('platform', existing_screen.platform)
                    existing_screen.locale = data.get('locale', existing_screen.locale)
                    existing_screen.is_active = data.get('is_active', existing_screen.is_active)
                    
                    db.commit()
                    print(f"🔄 Обновлен: {screen_name}")
                else:
                    screen = Screen(
                        name=screen_name,
                        title=data.get('title', ''),
                        description=data.get('description', ''),
                        config=data.get('config', {}),
                        platform=data.get('platform', 'web'),
                        locale=data.get('locale', 'ru'),
                        is_active=data.get('is_active', True)
                    )
                    
                    db.add(screen)
                    db.commit()
                    print(f"✅ Создан: {screen_name}")
                
                success_count += 1
                
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON в {filename}: {e}")
            except Exception as e:
                print(f"❌ Ошибка при обработке {filename}: {e}")
                db.rollback()
        
        if success_count > 0:
            print(f"🎉 Успешно обработано {success_count} экран(ов)!")
            return True
        else:
            print("⚠️  Не удалось обработать ни одного экрана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при загрузке экранов: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    load_screens_from_json()
