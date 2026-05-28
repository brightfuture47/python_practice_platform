import streamlit as st
import sqlite3
import json
from datetime import datetime

# ====================== БАЗА ДАННЫХ ======================
def init_db():
    conn = sqlite3.connect('tasks.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT,
        level TEXT,
        description TEXT,
        starter_code TEXT,
        test_cases TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS solutions (
        id INTEGER PRIMARY KEY,
        task_id INTEGER,
        code TEXT,
        timestamp TEXT,
        passed INTEGER
    )''')
    
    # Добавляем задачи, если их нет
    c.execute("SELECT COUNT(*) FROM tasks")
    if c.fetchone()[0] == 0:
        initial_tasks = [
            ("1. Сумма двух чисел", "Начинающий", 
             "Напишите функцию `sum_two_numbers(a, b)`, которая возвращает сумму двух чисел.",
             "def sum_two_numbers(a, b):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": [3, 5], "output": 8}, {"input": [-1, 7], "output": 6}])),

            ("2. Чётное или нечётное", "Начинающий",
             "Напишите функцию `is_even(number)`, которая возвращает `True`, если число чётное, иначе `False`.",
             "def is_even(number):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": [4], "output": True}, {"input": [7], "output": False}])),

            ("3. Перевернуть строку", "Начинающий",
             "Напишите функцию `reverse_string(s)`, которая возвращает строку в обратном порядке.",
             "def reverse_string(s):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": ["hello"], "output": "olleh"}, {"input": ["Python"], "output": "nohtyP"}])),

            ("4. Факториал числа", "intermediate",
             "Напишите функцию `factorial(n)`, которая вычисляет факториал числа.",
             "def factorial(n):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": [5], "output": 120}, {"input": [0], "output": 1}])),

            ("5. Поиск максимального числа в списке", "intermediate",
             "Напишите функцию `find_max(numbers)`, которая возвращает максимальное число в списке.",
             "def find_max(numbers):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": [[1, 5, 3, 9, 2]], "output": 9}, {"input": [[-1, -5]], "output": -1}])),

            ("6. Подсчёт гласных в строке", "intermediate",
             "Напишите функцию `count_vowels(s)`, которая считает количество гласных букв (а, е, и, о, у, ё, ы, э, ю, я).",
             "def count_vowels(s):\n    # Ваш код здесь\n    pass",
             json.dumps([{"input": ["hello"], "output": 2}, {"input": ["Python"], "output": 2}]))
        ]
        
        c.executemany("INSERT INTO tasks (title, level, description, starter_code, test_cases) VALUES (?,?,?,?,?)", initial_tasks)
    
    conn.commit()
    conn.close()

# ====================== ЗАПУСК КОДА ======================
def run_code(code, test_cases):
    try:
        local_env = {}
        exec(code, {"__builtins__": {}}, local_env)
        
        func_name = next((name for name in local_env if not name.startswith('__')), None)
        if not func_name:
            return [{"passed": False, "error": "Функция не найдена в коде"}]
        
        func = local_env[func_name]
        results = []
        
        for case in test_cases:
            try:
                result = func(*case["input"])
                passed = result == case["output"]
                results.append({
                    "passed": passed,
                    "input": case["input"],
                    "expected": case["output"],
                    "got": result
                })
            except Exception as e:
                results.append({"passed": False, "error": str(e)})
        
        return results
    except Exception as e:
        return [{"passed": False, "error": f"Ошибка выполнения: {str(e)}"}]

# ====================== ОСНОВНОЙ ИНТЕРФЕЙС ======================
st.set_page_config(page_title="Python Practice", layout="wide")
st.title("🐍 Python Practice Platform")
st.markdown("**Платформа для практики Python** — решай задачи и проверяй решения instantly!")

init_db()

# Навигация
tab1, tab2 = st.tabs(["📋 Список задач", "📜 Мои решения"])

with tab1:
    st.header("Доступные задачи")
    
    conn = sqlite3.connect('tasks.db')
    tasks = conn.execute("SELECT id, title, level FROM tasks").fetchall()
    conn.close()
    
    for task in tasks:
        level_color = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}.get(task[2], "⚪")
        
        col1, col2, col3 = st.columns([5, 1, 1])
        with col1:
            st.write(f"{level_color} **{task[1]}**")
        with col2:
            st.caption(task[2])
        with col3:
            if st.button("Решать", key=f"start_{task[0]}"):
                st.session_state.current_task = task[0]
                st.rerun()

    # Окно решения задачи
    if st.session_state.get("current_task"):
        task_id = st.session_state.current_task
        conn = sqlite3.connect('tasks.db')
        task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        conn.close()

        st.divider()
        st.header(task[1])
        st.markdown(task[3])  # description

        code = st.text_area("Напишите ваш код ниже:", task[4], height=280, key="code_input")

        if st.button("▶ Запустить и проверить", type="primary"):
            test_cases = json.loads(task[5])
            results = run_code(code, test_cases)
            
            all_passed = all(r.get("passed", False) for r in results if "passed" in r)
            
            if all_passed:
                st.success("🎉 Все тесты пройдены! Отличная работа!")
                passed_flag = 1
            else:
                st.error("❌ Не все тесты пройдены")
                passed_flag = 0

            # Сохраняем решение
            conn = sqlite3.connect('tasks.db')
            conn.execute("INSERT INTO solutions (task_id, code, timestamp, passed) VALUES (?,?,?,?)",
                        (task_id, code, datetime.now().strftime("%Y-%m-%d %H:%M"), passed_flag))
            conn.commit()
            conn.close()

            # Показываем результаты
            for i, r in enumerate(results):
                if "error" in r:
                    st.error(f"**Тест {i+1}**: Ошибка — {r['error']}")
                else:
                    status = "✅" if r["passed"] else "❌"
                    st.write(f"{status} **Тест {i+1}**: `{r['input']}` → Ожидалось `{r['expected']}`, получили `{r.get('got')}`")

with tab2:
    st.header("История ваших решений")
    conn = sqlite3.connect('tasks.db')
    solutions = conn.execute("""
        SELECT t.title, s.code, s.timestamp, s.passed 
        FROM solutions s 
        JOIN tasks t ON s.task_id = t.id 
        ORDER BY s.timestamp DESC
    """).fetchall()
    conn.close()

    if not solutions:
        st.info("Пока нет решённых задач. Решите первую!")
    else:
        for sol in solutions:
            status = "✅ Пройдено" if sol[3] else "❌ Не пройдено"
            with st.expander(f"{sol[0]} — {sol[2]} — {status}"):
                st.code(sol[1], language="python")

st.sidebar.success("Платформа работает локально. Всё сохраняется в tasks.db")