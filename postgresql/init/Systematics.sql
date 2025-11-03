--
-- PostgreSQL database dump
--

\restrict Cei8RD0lAMHEdJbkU4Yv5mjXlxAZe3ugQnirh4BpVvnaMgayNgfPk6gd0UcxndZ

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

-- Started on 2025-10-23 04:13:41

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ---------------------------------------------------------------------------
-- Introduce Constant / Consolidate Duplicate Code
\set ATTEMPT_STATUS_ENUM  '''in_progress'',''submitted'',''completed'''
\set QUESTION_TYPE_ENUM   '''single_choice'',''multi_choice'',''short_answer'',''long_answer'',''matching'''
-- ---------------------------------------------------------------------------

--
-- TOC entry 2 (class 3079 OID 16598)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

--
-- TOC entry 5085 (class 0 OID 0)
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner:
--
COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';

--
-- TOC entry 904 (class 1247 OID 16610)
-- Name: attempt_status_enum; Type: TYPE; Schema: public; Owner: postgres
--
CREATE TYPE public.attempt_status_enum AS ENUM ( :ATTEMPT_STATUS_ENUM );
ALTER TYPE public.attempt_status_enum OWNER TO postgres;

--
-- TOC entry 937 (class 1247 OID 16830)
-- Name: attemptstatus; Type: TYPE; Schema: public; Owner: postgres
--
CREATE TYPE public.attemptstatus AS ENUM ( :ATTEMPT_STATUS_ENUM );
ALTER TYPE public.attemptstatus OWNER TO postgres;

--
-- TOC entry 907 (class 1247 OID 16618)
-- Name: question_type_enum; Type: TYPE; Schema: public; Owner: postgres
--
CREATE TYPE public.question_type_enum AS ENUM ( :QUESTION_TYPE_ENUM );
ALTER TYPE public.question_type_enum OWNER TO postgres;

--
-- TOC entry 934 (class 1247 OID 16819)
-- Name: question_type_enum_weights; Type: TYPE; Schema: public; Owner: postgres
--
CREATE TYPE public.question_type_enum_weights AS ENUM ( :QUESTION_TYPE_ENUM );
ALTER TYPE public.question_type_enum_weights OWNER TO postgres;

--
-- TOC entry 922 (class 1247 OID 16737)
-- Name: questiontype; Type: TYPE; Schema: public; Owner: postgres
--
CREATE TYPE public.questiontype AS ENUM ( :QUESTION_TYPE_ENUM );
ALTER TYPE public.questiontype OWNER TO postgres;


ALTER TYPE public.questiontype OWNER TO postgres;

--
-- TOC entry 249 (class 1255 OID 16734)
-- Name: reorder_questions_on_delete(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.reorder_questions_on_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Оновлюємо позиції для всіх питань того ж іспиту,
    -- які йшли ПІСЛЯ видаленого питання.
    UPDATE questions
    SET position = position - 1
    WHERE exam_id = OLD.exam_id AND position > OLD.position;
    
    RETURN OLD; -- Повертаємо видалений запис
END;
$$;


ALTER FUNCTION public.reorder_questions_on_delete() OWNER TO postgres;

--
-- TOC entry 248 (class 1255 OID 16732)
-- Name: set_question_position_on_insert(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_question_position_on_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Знаходимо максимальне значення 'position' для конкретного exam_id,
    -- додаємо 1 і присвоюємо його новому запису.
    -- COALESCE(..., 0) обробляє випадок, коли це перше питання в іспиті.
    NEW.position := (
        SELECT COALESCE(MAX(position), 0) + 1
        FROM questions
        WHERE exam_id = NEW.exam_id
    );
    RETURN NEW; -- Повертаємо змінений запис для вставки
END;
$$;


ALTER FUNCTION public.set_question_position_on_insert() OWNER TO postgres;

--
-- TOC entry 247 (class 1255 OID 16730)
-- Name: update_exam_question_count_trigger(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_exam_question_count_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    exam_id_to_update UUID;
BEGIN
    -- Визначаємо, exam_id якого іспиту потрібно оновити
    -- TG_OP - це спеціальна змінна, яка містить тип операції ('INSERT', 'DELETE')
    IF (TG_OP = 'INSERT') THEN
        exam_id_to_update := NEW.exam_id; -- NEW - це рядок, що додається
    ELSIF (TG_OP = 'DELETE') THEN
        exam_id_to_update := OLD.exam_id; -- OLD - це рядок, що видаляється
    END IF;

    -- Перераховуємо кількість питань для цього іспиту і оновлюємо таблицю exams
    UPDATE exams
    SET question_count = (SELECT COUNT(*) FROM questions WHERE exam_id = exam_id_to_update)
    WHERE id = exam_id_to_update;

    -- Функція тригера має повернути NEW або OLD, або NULL
    RETURN NULL;
END;
$$;


ALTER FUNCTION public.update_exam_question_count_trigger() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 235 (class 1259 OID 16702)
-- Name: answer_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.answer_options (
    answer_id uuid NOT NULL,
    selected_option_id uuid NOT NULL
);


ALTER TABLE public.answer_options OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 16682)
-- Name: answers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.answers (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    attempt_id uuid NOT NULL,
    question_id uuid NOT NULL,
    answer_text text,
    answer_json jsonb,
    saved_at timestamp with time zone NOT NULL
);


ALTER TABLE public.answers OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16670)
-- Name: attempts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attempts (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    exam_id uuid NOT NULL,
    user_id uuid NOT NULL,
    status public.attempt_status_enum DEFAULT 'in_progress'::public.attempt_status_enum NOT NULL,
    started_at timestamp with time zone NOT NULL,
    submitted_at timestamp with time zone,
    due_at timestamp with time zone NOT NULL,
    time_spent_seconds integer,
    earned_points real,
    correct_answers integer,
    incorrect_answers integer,
    pending_count integer
);


ALTER TABLE public.attempts OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16541)
-- Name: course_exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.course_exams (
    course_id integer NOT NULL,
    exam_id uuid NOT NULL
);


ALTER TABLE public.course_exams OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16505)
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    id integer NOT NULL,
    name text NOT NULL,
    description text,
    code text NOT NULL
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16504)
-- Name: courses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.courses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.courses_id_seq OWNER TO postgres;

--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 225
-- Name: courses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.courses_id_seq OWNED BY public.courses.id;


--
-- TOC entry 228 (class 1259 OID 16534)
-- Name: exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exams (
    id uuid NOT NULL,
    title text NOT NULL,
    instructions text,
    start_at timestamp with time zone NOT NULL,
    end_at timestamp with time zone NOT NULL,
    max_attempts integer NOT NULL,
    pass_threshold integer NOT NULL,
    owner_id uuid NOT NULL,
    question_count integer NOT NULL,
    duration_minutes integer NOT NULL
);


ALTER TABLE public.exams OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16463)
-- Name: login_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.login_history (
    id bigint NOT NULL,
    user_id uuid NOT NULL,
    login_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    ip_address text
);


ALTER TABLE public.login_history OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16462)
-- Name: login_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.login_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.login_history_id_seq OWNER TO postgres;

--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 223
-- Name: login_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.login_history_id_seq OWNED BY public.login_history.id;


--
-- TOC entry 227 (class 1259 OID 16515)
-- Name: major_courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.major_courses (
    major_id integer NOT NULL,
    course_id integer NOT NULL
);


ALTER TABLE public.major_courses OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 16411)
-- Name: majors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.majors (
    id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.majors OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16410)
-- Name: majors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.majors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.majors_id_seq OWNER TO postgres;

--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 218
-- Name: majors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.majors_id_seq OWNED BY public.majors.id;


--
-- TOC entry 232 (class 1259 OID 16657)
-- Name: matching_pairs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matching_pairs (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    question_id uuid NOT NULL,
    prompt text NOT NULL,
    correct_match text NOT NULL
);


ALTER TABLE public.matching_pairs OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 16643)
-- Name: options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.options (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    question_id uuid NOT NULL,
    text text NOT NULL,
    is_correct boolean DEFAULT false NOT NULL
);


ALTER TABLE public.options OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 16723)
-- Name: question_type_weights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_type_weights (
    question_type public.question_type_enum NOT NULL,
    weight integer NOT NULL,
    CONSTRAINT question_type_weights_weight_check CHECK ((weight > 0))
);


ALTER TABLE public.question_type_weights OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 16629)
-- Name: questions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.questions (
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    exam_id uuid NOT NULL,
    question_type public.question_type_enum NOT NULL,
    title text NOT NULL,
    "position" integer,
    points integer
);


ALTER TABLE public.questions OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 16400)
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 16399)
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_seq OWNER TO postgres;

--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 216
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- TOC entry 222 (class 1259 OID 16447)
-- Name: user_majors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_majors (
    user_id uuid NOT NULL,
    major_id integer NOT NULL
);


ALTER TABLE public.user_majors OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16432)
-- Name: user_roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id integer NOT NULL
);


ALTER TABLE public.user_roles OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16421)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email text NOT NULL,
    hashed_password text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    first_name text NOT NULL,
    last_name text NOT NULL,
    patronymic text
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 4837 (class 2604 OID 16508)
-- Name: courses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses ALTER COLUMN id SET DEFAULT nextval('public.courses_id_seq'::regclass);


--
-- TOC entry 4835 (class 2604 OID 16466)
-- Name: login_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history ALTER COLUMN id SET DEFAULT nextval('public.login_history_id_seq'::regclass);


--
-- TOC entry 4832 (class 2604 OID 16414)
-- Name: majors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors ALTER COLUMN id SET DEFAULT nextval('public.majors_id_seq'::regclass);


--
-- TOC entry 4831 (class 2604 OID 16403)
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- TOC entry 5078 (class 0 OID 16702)
-- Dependencies: 235
-- Data for Name: answer_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answer_options (answer_id, selected_option_id) FROM stdin;
\.


--
-- TOC entry 5077 (class 0 OID 16682)
-- Dependencies: 234
-- Data for Name: answers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answers (id, attempt_id, question_id, answer_text, answer_json, saved_at) FROM stdin;
\.


--
-- TOC entry 5076 (class 0 OID 16670)
-- Dependencies: 233
-- Data for Name: attempts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attempts (id, exam_id, user_id, status, started_at, submitted_at, due_at, time_spent_seconds, earned_points, correct_answers, incorrect_answers, pending_count) FROM stdin;
\.


--
-- TOC entry 5072 (class 0 OID 16541)
-- Dependencies: 229
-- Data for Name: course_exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.course_exams (course_id, exam_id) FROM stdin;
1	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
1	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f
2	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e
2	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b
2	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
3	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a
3	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
3	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f
\.


--
-- TOC entry 5069 (class 0 OID 16505)
-- Dependencies: 226
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (id, name, description, code) FROM stdin;
1	Основи програмування	Вступ до Python та структур даних.	CS101
2	Алгоритми та структури даних	Аналіз ефективності алгоритмів, сортування, графи.	CS201
3	Бази даних та SQL	Проектування реляційних баз даних та запити.	CS305
4	Диференціальні рівняння	Теорія та методи розв'язання диференціальних рівнянь.	AM204
5	Чисельні методи	Наближені методи розв'язання математичних задач.	AM310
6	Теорія ймовірностей	Основи статистичного аналізу та випадкові процеси.	AM101
7	Патерни проектування	Вивчення класичних архітектурних рішень.	SE315
8	Вступ до QA та тестування	Принципи забезпечення якості та методи тестування ПЗ.	SE202
9	Управління вимогами	Збір, аналіз та документування вимог до ПЗ.	SE401
\.


--
-- TOC entry 5071 (class 0 OID 16534)
-- Dependencies: 228
-- Data for Name: exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.exams (id, title, instructions, start_at, end_at, max_attempts, pass_threshold, owner_id, question_count, duration_minutes) FROM stdin;
c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	Іспит з "Організації баз даних"	Дозволено користуватися власними нотатками, зробленими від руки.	2026-01-15 14:00:00+02	2026-01-15 16:00:00+02	1	70	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	120
d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	Залік з "Основ тестування програмного забезпечення"	Залік складається з тестової частини (20 питань) та практичного завдання (написання тест-кейсів).	2026-01-18 11:00:00+02	2026-01-18 13:00:00+02	3	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	120
e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	Іспит з "Лінійної алгебри та аналітичної геометрії"	При собі мати калькулятор. Використання мобільних телефонів заборонено.	2025-12-22 16:00:00+02	2025-12-22 18:00:00+02	1	55	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	120
b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	Модульний контроль №2 з "Математичного аналізу"	\N	2025-11-25 12:00:00+02	2025-11-25 13:30:00+02	2	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	90
a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	Підсумковий іспит з "Алгоритми та структури даних"	Іспит складається з 30 теоретичних питань та 2 практичних завдань. Час на виконання - 120 хвилин.	2025-10-15 12:00:00+03	2025-12-20 13:00:00+02	1	65	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	4	120
\.


--
-- TOC entry 5067 (class 0 OID 16463)
-- Dependencies: 224
-- Data for Name: login_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_history (id, user_id, login_timestamp, ip_address) FROM stdin;
\.


--
-- TOC entry 5070 (class 0 OID 16515)
-- Dependencies: 227
-- Data for Name: major_courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.major_courses (major_id, course_id) FROM stdin;
1	1
1	2
1	3
2	4
2	5
2	6
3	7
3	8
3	9
\.


--
-- TOC entry 5062 (class 0 OID 16411)
-- Dependencies: 219
-- Data for Name: majors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.majors (id, name) FROM stdin;
1	Комп'ютерні науки
2	Прикладна математика
3	Інженерія програмного забезпечення
\.


--
-- TOC entry 5075 (class 0 OID 16657)
-- Dependencies: 232
-- Data for Name: matching_pairs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.matching_pairs (id, question_id, prompt, correct_match) FROM stdin;
3200fcf3-1710-4669-a829-e9e938a6b52a	b5130cc8-1837-4715-9749-68b879fd5f5d	Довжина вектора a = (x, y, z)	√(x² + y² + z²)
2a7844c8-e832-41e6-824e-d0e692aed0af	b5130cc8-1837-4715-9749-68b879fd5f5d	Скалярний добуток векторів a та b	|a| * |b| * cos(θ)
fce9f001-6837-4946-aaa4-c67b2ff2421d	b5130cc8-1837-4715-9749-68b879fd5f5d	Рівняння площини	Ax + By + Cz + D = 0
d596c707-43f7-4e2d-b378-671898171681	ba3e241d-aeec-43a4-8086-f2c025d3a35a	sin(x)	cos(x)
48615634-71f4-4d50-bab2-d960e6a1cc18	ba3e241d-aeec-43a4-8086-f2c025d3a35a	cos(x)	-sin(x)
90e6689d-1596-4c66-9833-c8631f22435c	ba3e241d-aeec-43a4-8086-f2c025d3a35a	ln(x)	1/x
3b416388-a4bc-411e-90ed-53437ec1ee16	292f04a8-5cf8-44b8-bc40-36c68437dfd9	Модульне тестування	Перевірка окремих функцій або компонентів коду.
72f2411c-3aba-400d-a5a6-a9aef91b2877	292f04a8-5cf8-44b8-bc40-36c68437dfd9	Інтеграційне тестування	Перевірка взаємодії між кількома модулями.
78ab8790-b997-4486-b4f0-c49d3a66e296	292f04a8-5cf8-44b8-bc40-36c68437dfd9	Системне тестування	Перевірка всієї системи як єдиного цілого.
\.


--
-- TOC entry 5074 (class 0 OID 16643)
-- Dependencies: 231
-- Data for Name: options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.options (id, question_id, text, is_correct) FROM stdin;
c23081f2-b9f5-4b2b-b084-64f57eb45bb6	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	ad - bc	t
8a4e266e-46fc-4b12-be12-55ffa98fb4fb	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	ac - bd	f
400ac254-7799-4170-943b-90cf03de6c09	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	ad + bc	f
168011c4-b118-4957-a4f8-732912358ec1	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	ab - cd	f
bc16b8b2-af2f-4956-b570-c0e811dc53da	8e45a053-35f9-4c82-a9ad-dfa4fac62137	Скалярний добуток ортогональних векторів дорівнює нулю.	t
8b24c98e-3a1e-438c-b7c4-f6f91a8b7d1b	8e45a053-35f9-4c82-a9ad-dfa4fac62137	Колінеарні вектори завжди мають однакову довжину.	f
7f8dfce9-cbb3-4a77-bea2-72b7484fc637	8e45a053-35f9-4c82-a9ad-dfa4fac62137	Векторний добуток двох колінеарних векторів є нуль-вектором.	t
cabea420-6eb2-44c4-93a4-cc463e95b315	8e45a053-35f9-4c82-a9ad-dfa4fac62137	Довжина вектора може бути від'ємною.	f
164431b5-a5d8-49e1-921d-9004b107fa3d	0b6926df-8c4e-413f-a7ee-66cd7b4de6b8	1	t
58c172e6-921c-49fa-bf0a-66b6f075aeb1	c66488df-9d33-4e77-aab6-320762a544eb	O(n)	f
1af47804-e5e6-4f3f-a807-6fccbc5b1d55	c66488df-9d33-4e77-aab6-320762a544eb	O(log n)	t
a42b7084-2cde-4ca4-bf3b-3e4e8e8a918a	c66488df-9d33-4e77-aab6-320762a544eb	O(n^2)	f
13e28ff4-88fc-40b1-ab30-f56f4dc681da	c66488df-9d33-4e77-aab6-320762a544eb	O(1)	f
59cae28f-4beb-4768-a3ac-f0d94597ed96	54ae4cd3-f8ba-4997-9369-bcacc6981907	Черга (Queue)	f
bc65a758-5552-4d1b-a978-3824383c7118	54ae4cd3-f8ba-4997-9369-bcacc6981907	Стек (Stack)	t
459b99ce-0469-48b0-8a19-b09b18752a51	54ae4cd3-f8ba-4997-9369-bcacc6981907	Зв'язаний список (Linked List)	f
b2752c6e-7a2e-447a-8452-14b0e6c03e51	54ae4cd3-f8ba-4997-9369-bcacc6981907	Стек викликів (Call Stack)	t
1778c1a1-4988-4102-907b-996a4e571996	8ac581ea-4236-456f-b917-c71bfda342fb	Словник	t
72dd0aca-1b7a-4890-88c6-60c37c919b7e	8ac581ea-4236-456f-b917-c71bfda342fb	Хеш-таблиця	t
bf6c10b5-ca69-497f-9d1b-8552e74de0c8	8ac581ea-4236-456f-b917-c71bfda342fb	Асоціативний масив	t
02bcbecb-1521-4b31-ae59-92b6e32e9b76	b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	3x	f
5a838798-3355-4332-8b4e-28bb3d656af9	b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	3x²	t
58b3ec94-ffa6-4164-847f-835905e9174c	b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	x²/2	f
0f38ba70-2170-4cd3-80aa-4d482c082ec5	b9c9df43-6293-487a-84ef-d925a6d047e3	0	t
557d6fc8-6f8d-45ab-aa4a-faecdfef71f7	e9c4b680-8443-43e0-b05e-e8a56f61d40d	GET	f
deea8e65-a1ae-4374-b6f3-2cb3a14db7f4	e9c4b680-8443-43e0-b05e-e8a56f61d40d	SELECT	t
a76c5ad1-3461-447f-b500-3c4caea60cdb	e9c4b680-8443-43e0-b05e-e8a56f61d40d	FETCH	f
1f081516-122f-416b-98f9-92d357942333	e9c4b680-8443-43e0-b05e-e8a56f61d40d	OPEN	f
b2f8ce79-2ef7-4f08-b070-1868211a3de0	a599186c-5893-4137-ada0-3aa79fd902ee	SELECT	f
3b896b82-3d69-460f-82dd-e89855b7526f	a599186c-5893-4137-ada0-3aa79fd902ee	CREATE TABLE	t
e149dd3e-086e-4b1c-8463-79ff8227adf7	a599186c-5893-4137-ada0-3aa79fd902ee	INSERT	f
0da5b2f0-3ffe-4eeb-b63a-d442ddefa9e6	a599186c-5893-4137-ada0-3aa79fd902ee	ALTER TABLE	t
ee37a384-fb57-48d0-af1e-5961756c654d	a599186c-5893-4137-ada0-3aa79fd902ee	DROP VIEW	t
b157b137-bcf2-45c2-a63e-512ad657e7aa	c6dd6bbd-c488-4b91-b381-d909ab836795	Функціональне тестування	f
4006f586-0fe5-47a5-a21b-38a037a72ec6	c6dd6bbd-c488-4b91-b381-d909ab836795	Регресійне тестування	t
4a62000c-3fca-4e6f-926d-75eed944df1e	c6dd6bbd-c488-4b91-b381-d909ab836795	Тестування навантаження	f
eddedd1e-e187-4eb5-a43b-f13afe1e5eaa	32ea01f5-33ec-4ff8-891a-b48349f9078a	Тестування продуктивності (Performance Testing)	t
d9757a3e-bdb3-4ac4-9b27-f842691931f0	32ea01f5-33ec-4ff8-891a-b48349f9078a	Тестування юзабіліті (Usability Testing)	t
b5d07d28-d5e5-4bd3-ba22-65771cbe028b	32ea01f5-33ec-4ff8-891a-b48349f9078a	Модульне тестування (Unit Testing)	f
39662166-b7bd-42e3-87f9-0c6a6cf67523	32ea01f5-33ec-4ff8-891a-b48349f9078a	Тестування безпеки (Security Testing)	t
\.


--
-- TOC entry 5079 (class 0 OID 16723)
-- Dependencies: 236
-- Data for Name: question_type_weights; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.question_type_weights (question_type, weight) FROM stdin;
single_choice	1
multi_choice	2
short_answer	2
matching	3
long_answer	5
\.


--
-- TOC entry 5073 (class 0 OID 16629)
-- Dependencies: 230
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (id, exam_id, question_type, title, "position", points) FROM stdin;
54ae4cd3-f8ba-4997-9369-bcacc6981907	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	multi_choice	Які з наведених структур даних працюють за принципом LIFO (Last-In, First-Out)?	2	2
57d4d112-26c3-4c36-b03a-9c671471193a	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	long_answer	Поясніть своїми словами різницю між масивом (Array) та зв'язаним списком (Linked List), вказавши переваги та недоліки кожного.	4	5
292f04a8-5cf8-44b8-bc40-36c68437dfd9	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	matching	Встановіть відповідність між рівнем тестування та його описом.	3	3
32ea01f5-33ec-4ff8-891a-b48349f9078a	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	multi_choice	Які з наведених видів тестування належать до нефункціональних?	2	2
c6dd6bbd-c488-4b91-b381-d909ab836795	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	single_choice	Який вид тестування виконується для перевірки того, що нові зміни не зламали існуючий функціонал?	1	1
732eb6fb-2faf-41ee-979f-c7e0aa2d454f	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	long_answer	Опишіть, що таке перша нормальна форма (1НФ) в реляційних базах даних.	3	5
a599186c-5893-4137-ada0-3aa79fd902ee	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	multi_choice	Які з наведених операторів належать до DDL (Data Definition Language)?	2	2
e9c4b680-8443-43e0-b05e-e8a56f61d40d	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	single_choice	Яка команда SQL використовується для вибірки даних з бази даних?	1	1
8ac581ea-4236-456f-b917-c71bfda342fb	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	short_answer	Як називається структура даних, яка зберігає пари "ключ-значення"?	3	2
c66488df-9d33-4e77-aab6-320762a544eb	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	single_choice	Яка часова складність алгоритму бінарного пошуку в відсортованому масиві?	1	1
0b6926df-8c4e-413f-a7ee-66cd7b4de6b8	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	short_answer	Знайдіть ранг матриці [[1, 2, 3], [2, 4, 6]]. Введіть відповідь у вигляді числа.	3	2
16e8b1f9-af8f-4b56-9bbd-d65d6a658526	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	single_choice	Чому дорівнює визначник (детермінант) матриці [[a, b], [c, d]]?	1	1
86eb5e7f-2889-417c-84b7-4833fb7656e7	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	long_answer	Поясніть своїми словами, що таке власні вектори та власні значення матриці.	4	5
8e45a053-35f9-4c82-a9ad-dfa4fac62137	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	multi_choice	Які з наступних тверджень про вектори є вірними?	2	2
b5130cc8-1837-4715-9749-68b879fd5f5d	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	matching	Встановіть відповідність між поняттям та його математичним виразом.	5	3
b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	single_choice	Чому дорівнює похідна функції f(x) = x³?	1	1
b9c9df43-6293-487a-84ef-d925a6d047e3	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	short_answer	Обчисліть границю lim(x->∞) (1/x).	2	2
ba3e241d-aeec-43a4-8086-f2c025d3a35a	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	matching	Встановіть відповідність між функцією та її похідною.	3	3
\.


--
-- TOC entry 5060 (class 0 OID 16400)
-- Dependencies: 217
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name) FROM stdin;
1	student
2	teacher
3	supervisor
\.


--
-- TOC entry 5065 (class 0 OID 16447)
-- Dependencies: 222
-- Data for Name: user_majors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_majors (user_id, major_id) FROM stdin;
a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	1
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	2
bed7d3a1-8461-41fa-9610-03db8bc58a85	3
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	1
\.


--
-- TOC entry 5064 (class 0 OID 16432)
-- Dependencies: 221
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_roles (user_id, role_id) FROM stdin;
bed7d3a1-8461-41fa-9610-03db8bc58a85	1
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	1
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	1
a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	2
\.


--
-- TOC entry 5063 (class 0 OID 16421)
-- Dependencies: 220
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, created_at, first_name, last_name, patronymic) FROM stdin;
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	miroslava.flom@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:15:27.673607+03	Мирослава	Фломбойм	Олексіївна
a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	minelenova1@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:01:19.539414+03	Олександра	Малій	Михайлівна
bed7d3a1-8461-41fa-9610-03db8bc58a85	chulano10@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:14:50.302061+03	Владислава	Колінько	Володимирівна
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	anastasiabakalyna@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:15:06.219423+03	Анастасія	Бакалина	Ярославівна
\.


--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 225
-- Name: courses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_id_seq', 9, true);


--
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 223
-- Name: login_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.login_history_id_seq', 1, false);


--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 218
-- Name: majors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.majors_id_seq', 4, true);


--
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 216
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_seq', 8, true);


--
-- TOC entry 4873 (class 2606 OID 16545)
-- Name: course_exams course_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_pkey PRIMARY KEY (course_id, exam_id);


--
-- TOC entry 4865 (class 2606 OID 16514)
-- Name: courses courses_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_code_key UNIQUE (code);


--
-- TOC entry 4867 (class 2606 OID 16512)
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- TOC entry 4884 (class 2606 OID 16676)
-- Name: attempts exam_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT exam_attempts_pkey PRIMARY KEY (id);


--
-- TOC entry 4871 (class 2606 OID 16540)
-- Name: exams exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (id);


--
-- TOC entry 4863 (class 2606 OID 16471)
-- Name: login_history login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4869 (class 2606 OID 16519)
-- Name: major_courses major_courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_pkey PRIMARY KEY (major_id, course_id);


--
-- TOC entry 4851 (class 2606 OID 16420)
-- Name: majors majors_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_name_key UNIQUE (name);


--
-- TOC entry 4853 (class 2606 OID 16418)
-- Name: majors majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_pkey PRIMARY KEY (id);


--
-- TOC entry 4882 (class 2606 OID 16664)
-- Name: matching_pairs matching_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_pairs
    ADD CONSTRAINT matching_pairs_pkey PRIMARY KEY (id);


--
-- TOC entry 4879 (class 2606 OID 16651)
-- Name: options options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.options
    ADD CONSTRAINT options_pkey PRIMARY KEY (id);


--
-- TOC entry 4895 (class 2606 OID 16728)
-- Name: question_type_weights question_type_weights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_type_weights
    ADD CONSTRAINT question_type_weights_pkey PRIMARY KEY (question_type);


--
-- TOC entry 4876 (class 2606 OID 16637)
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- TOC entry 4847 (class 2606 OID 16409)
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 4849 (class 2606 OID 16407)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 4893 (class 2606 OID 16706)
-- Name: answer_options student_answer_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_pkey PRIMARY KEY (answer_id, selected_option_id);


--
-- TOC entry 4889 (class 2606 OID 16691)
-- Name: answers student_answers_attempt_id_question_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_attempt_id_question_id_key UNIQUE (attempt_id, question_id);


--
-- TOC entry 4891 (class 2606 OID 16689)
-- Name: answers student_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_pkey PRIMARY KEY (id);


--
-- TOC entry 4861 (class 2606 OID 16451)
-- Name: user_majors user_majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4859 (class 2606 OID 16436)
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- TOC entry 4855 (class 2606 OID 16431)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4857 (class 2606 OID 16429)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4885 (class 1259 OID 16721)
-- Name: idx_exam_attempts_on_exam_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_attempts_on_exam_id ON public.attempts USING btree (exam_id);


--
-- TOC entry 4886 (class 1259 OID 16720)
-- Name: idx_exam_attempts_on_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_attempts_on_user_id ON public.attempts USING btree (user_id);


--
-- TOC entry 4880 (class 1259 OID 16719)
-- Name: idx_matching_pairs_on_question_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matching_pairs_on_question_id ON public.matching_pairs USING btree (question_id);


--
-- TOC entry 4877 (class 1259 OID 16718)
-- Name: idx_options_on_question_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_options_on_question_id ON public.options USING btree (question_id);


--
-- TOC entry 4874 (class 1259 OID 16717)
-- Name: idx_questions_on_exam_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_on_exam_id ON public.questions USING btree (exam_id);


--
-- TOC entry 4887 (class 1259 OID 16722)
-- Name: idx_student_answers_on_attempt_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answers_on_attempt_id ON public.answers USING btree (attempt_id);


--
-- TOC entry 4913 (class 2620 OID 16731)
-- Name: questions questions_count_update_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_count_update_trigger AFTER INSERT OR DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.update_exam_question_count_trigger();


--
-- TOC entry 4914 (class 2620 OID 16735)
-- Name: questions questions_reorder_after_delete; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_reorder_after_delete AFTER DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.reorder_questions_on_delete();


--
-- TOC entry 4915 (class 2620 OID 16733)
-- Name: questions questions_set_position_before_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_set_position_before_insert BEFORE INSERT ON public.questions FOR EACH ROW EXECUTE FUNCTION public.set_question_position_on_insert();


--
-- TOC entry 4903 (class 2606 OID 16546)
-- Name: course_exams course_exams_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4904 (class 2606 OID 16551)
-- Name: course_exams course_exams_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4908 (class 2606 OID 16677)
-- Name: attempts exam_attempts_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT exam_attempts_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4900 (class 2606 OID 16472)
-- Name: login_history login_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4901 (class 2606 OID 16525)
-- Name: major_courses major_courses_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4902 (class 2606 OID 16520)
-- Name: major_courses major_courses_major_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.majors(id) ON DELETE CASCADE;


--
-- TOC entry 4907 (class 2606 OID 16665)
-- Name: matching_pairs matching_pairs_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_pairs
    ADD CONSTRAINT matching_pairs_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4906 (class 2606 OID 16652)
-- Name: options options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.options
    ADD CONSTRAINT options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4905 (class 2606 OID 16638)
-- Name: questions questions_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4911 (class 2606 OID 16712)
-- Name: answer_options student_answer_options_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.options(id) ON DELETE CASCADE;


--
-- TOC entry 4912 (class 2606 OID 16707)
-- Name: answer_options student_answer_options_student_answer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_student_answer_id_fkey FOREIGN KEY (answer_id) REFERENCES public.answers(id) ON DELETE CASCADE;


--
-- TOC entry 4909 (class 2606 OID 16692)
-- Name: answers student_answers_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.attempts(id) ON DELETE CASCADE;


--
-- TOC entry 4910 (class 2606 OID 16697)
-- Name: answers student_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4898 (class 2606 OID 16457)
-- Name: user_majors user_majors_major_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.majors(id) ON DELETE RESTRICT;


--
-- TOC entry 4899 (class 2606 OID 16452)
-- Name: user_majors user_majors_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4896 (class 2606 OID 16442)
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE RESTRICT;


--
-- TOC entry 4897 (class 2606 OID 16437)
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-10-23 04:13:41

--
-- PostgreSQL database dump complete
--

\unrestrict Cei8RD0lAMHEdJbkU4Yv5mjXlxAZe3ugQnirh4BpVvnaMgayNgfPk6gd0UcxndZ

