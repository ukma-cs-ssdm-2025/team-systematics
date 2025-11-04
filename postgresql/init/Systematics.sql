--
-- PostgreSQL database dump
--

\restrict 3pXITESzWB9cubE6jWqg5hq6euBMg8j7Reh68vT7QPeEA2Kpcg4xFxUWpuznJLP

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

-- Started on 2025-11-04 23:02:10

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

--
-- TOC entry 2 (class 3079 OID 16598)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 904 (class 1247 OID 16610)
-- Name: attempt_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attempt_status_enum AS ENUM (
    'in_progress',
    'submitted',
    'completed'
);


ALTER TYPE public.attempt_status_enum OWNER TO postgres;

--
-- TOC entry 937 (class 1247 OID 16830)
-- Name: attemptstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attemptstatus AS ENUM (
    'in_progress',
    'submitted',
    'completed'
);


ALTER TYPE public.attemptstatus OWNER TO postgres;

--
-- TOC entry 907 (class 1247 OID 16618)
-- Name: question_type_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.question_type_enum AS ENUM (
    'single_choice',
    'multi_choice',
    'short_answer',
    'long_answer',
    'matching'
);


ALTER TYPE public.question_type_enum OWNER TO postgres;

--
-- TOC entry 934 (class 1247 OID 16819)
-- Name: question_type_enum_weights; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.question_type_enum_weights AS ENUM (
    'single_choice',
    'multi_choice',
    'short_answer',
    'long_answer',
    'matching'
);


ALTER TYPE public.question_type_enum_weights OWNER TO postgres;

--
-- TOC entry 922 (class 1247 OID 16737)
-- Name: questiontype; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.questiontype AS ENUM (
    'single_choice',
    'multi_choice',
    'short_answer',
    'long_answer',
    'matching'
);


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
-- TOC entry 234 (class 1259 OID 16702)
-- Name: answer_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.answer_options (
    answer_id uuid NOT NULL,
    selected_option_id uuid NOT NULL
);


ALTER TABLE public.answer_options OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 16682)
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
-- TOC entry 232 (class 1259 OID 16670)
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
-- TOC entry 236 (class 1259 OID 16838)
-- Name: course_enrollments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.course_enrollments (
    user_id uuid NOT NULL,
    course_id uuid NOT NULL
);


ALTER TABLE public.course_enrollments OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16541)
-- Name: course_exams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.course_exams (
    exam_id uuid NOT NULL,
    course_id uuid NOT NULL
);


ALTER TABLE public.course_exams OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16505)
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    name text NOT NULL,
    description text,
    code text NOT NULL,
    id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    owner_id uuid NOT NULL
);


ALTER TABLE public.courses OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16534)
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
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 223
-- Name: login_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.login_history_id_seq OWNED BY public.login_history.id;


--
-- TOC entry 226 (class 1259 OID 16515)
-- Name: major_courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.major_courses (
    major_id integer NOT NULL,
    course_id uuid
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
-- TOC entry 5094 (class 0 OID 0)
-- Dependencies: 218
-- Name: majors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.majors_id_seq OWNED BY public.majors.id;


--
-- TOC entry 231 (class 1259 OID 16657)
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
-- TOC entry 230 (class 1259 OID 16643)
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
-- TOC entry 235 (class 1259 OID 16723)
-- Name: question_type_weights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.question_type_weights (
    question_type public.question_type_enum NOT NULL,
    weight integer NOT NULL,
    CONSTRAINT question_type_weights_weight_check CHECK ((weight > 0))
);


ALTER TABLE public.question_type_weights OWNER TO postgres;

--
-- TOC entry 229 (class 1259 OID 16629)
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
-- TOC entry 5095 (class 0 OID 0)
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
    patronymic text,
    notification_settings jsonb DEFAULT '{"enabled": false, "remind_before_hours": []}'::jsonb NOT NULL,
    avatar_url character varying(255)
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 4839 (class 2604 OID 16466)
-- Name: login_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history ALTER COLUMN id SET DEFAULT nextval('public.login_history_id_seq'::regclass);


--
-- TOC entry 4835 (class 2604 OID 16414)
-- Name: majors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors ALTER COLUMN id SET DEFAULT nextval('public.majors_id_seq'::regclass);


--
-- TOC entry 4834 (class 2604 OID 16403)
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- TOC entry 5084 (class 0 OID 16702)
-- Dependencies: 234
-- Data for Name: answer_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answer_options (answer_id, selected_option_id) FROM stdin;
d98e2825-1947-411e-9d0a-4198459a9db7	4006f586-0fe5-47a5-a21b-38a037a72ec6
9cbb60fc-a4da-4d70-a4e6-50ed7ca6a578	39662166-b7bd-42e3-87f9-0c6a6cf67523
9cbb60fc-a4da-4d70-a4e6-50ed7ca6a578	eddedd1e-e187-4eb5-a43b-f13afe1e5eaa
9cbb60fc-a4da-4d70-a4e6-50ed7ca6a578	d9757a3e-bdb3-4ac4-9b27-f842691931f0
4efc0923-3d53-48d6-910c-353b0da45d0c	4006f586-0fe5-47a5-a21b-38a037a72ec6
625900d9-ff5e-480d-9711-07fed02d568f	d9757a3e-bdb3-4ac4-9b27-f842691931f0
625900d9-ff5e-480d-9711-07fed02d568f	eddedd1e-e187-4eb5-a43b-f13afe1e5eaa
625900d9-ff5e-480d-9711-07fed02d568f	39662166-b7bd-42e3-87f9-0c6a6cf67523
f4151b70-9e8f-4d98-bcfc-86fa06a0af25	5a838798-3355-4332-8b4e-28bb3d656af9
a2b6ba9f-315b-483d-ab6c-0ceb9e3b9f6c	4006f586-0fe5-47a5-a21b-38a037a72ec6
b5980df8-eef5-4a2e-ba39-19d0d2630182	eddedd1e-e187-4eb5-a43b-f13afe1e5eaa
b5980df8-eef5-4a2e-ba39-19d0d2630182	d9757a3e-bdb3-4ac4-9b27-f842691931f0
b5980df8-eef5-4a2e-ba39-19d0d2630182	39662166-b7bd-42e3-87f9-0c6a6cf67523
866fd0e5-5575-47c5-bef8-f5bb4ce2fe29	1af47804-e5e6-4f3f-a807-6fccbc5b1d55
e015b591-0ee6-453d-b473-061acb85ad05	59cae28f-4beb-4768-a3ac-f0d94597ed96
e015b591-0ee6-453d-b473-061acb85ad05	bc65a758-5552-4d1b-a978-3824383c7118
e015b591-0ee6-453d-b473-061acb85ad05	b2752c6e-7a2e-447a-8452-14b0e6c03e51
c232f4fb-9bd8-47ef-88c7-2cf5f79912fa	02db3b4e-f775-4b46-9fa5-39a2ecc941e8
340ed609-93a3-465a-83a2-065a219cb5a4	309c89b1-ad92-4d43-a02f-cea8f446b542
\.


--
-- TOC entry 5083 (class 0 OID 16682)
-- Dependencies: 233
-- Data for Name: answers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answers (id, attempt_id, question_id, answer_text, answer_json, saved_at) FROM stdin;
2c715772-3c48-4ee1-bcf3-2a68b1c32938	f5565c5c-9fdf-4b99-aed7-aba85403a485	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	{"3b416388-a4bc-411e-90ed-53437ec1ee16": "3b416388-a4bc-411e-90ed-53437ec1ee16", "72f2411c-3aba-400d-a5a6-a9aef91b2877": "72f2411c-3aba-400d-a5a6-a9aef91b2877", "78ab8790-b997-4486-b4f0-c49d3a66e296": "78ab8790-b997-4486-b4f0-c49d3a66e296"}	2025-11-01 23:49:33.573216+02
f4151b70-9e8f-4d98-bcfc-86fa06a0af25	8eb2265f-4a06-4fc5-a751-992b6d80c439	b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	\N	null	2025-11-02 23:51:25.366458+02
d2a2fae1-2cef-4522-9aee-72b6c16d672c	8eb2265f-4a06-4fc5-a751-992b6d80c439	b9c9df43-6293-487a-84ef-d925a6d047e3	0	0	2025-11-02 23:51:27.469809+02
fd605170-239d-4dd6-9979-17e93773963a	8eb2265f-4a06-4fc5-a751-992b6d80c439	ba3e241d-aeec-43a4-8086-f2c025d3a35a	\N	{"48615634-71f4-4d50-bab2-d960e6a1cc18": "48615634-71f4-4d50-bab2-d960e6a1cc18", "90e6689d-1596-4c66-9833-c8631f22435c": "90e6689d-1596-4c66-9833-c8631f22435c", "d596c707-43f7-4e2d-b378-671898171681": "d596c707-43f7-4e2d-b378-671898171681"}	2025-11-02 23:51:31.945627+02
a2b6ba9f-315b-483d-ab6c-0ceb9e3b9f6c	47b8a08c-f47c-4eed-8078-aec7f18d79b9	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-11-04 20:06:25.598358+02
b5980df8-eef5-4a2e-ba39-19d0d2630182	47b8a08c-f47c-4eed-8078-aec7f18d79b9	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-11-04 20:06:28.433393+02
92eabeda-d86b-4c14-a932-62c42d4346ee	47b8a08c-f47c-4eed-8078-aec7f18d79b9	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	{"3b416388-a4bc-411e-90ed-53437ec1ee16": "3b416388-a4bc-411e-90ed-53437ec1ee16", "72f2411c-3aba-400d-a5a6-a9aef91b2877": "72f2411c-3aba-400d-a5a6-a9aef91b2877", "78ab8790-b997-4486-b4f0-c49d3a66e296": "78ab8790-b997-4486-b4f0-c49d3a66e296"}	2025-11-04 20:06:51.165502+02
866fd0e5-5575-47c5-bef8-f5bb4ce2fe29	1cb1b846-0ed5-46b1-95d8-093ef809dc37	c66488df-9d33-4e77-aab6-320762a544eb	\N	null	2025-11-04 20:07:18.906306+02
e015b591-0ee6-453d-b473-061acb85ad05	1cb1b846-0ed5-46b1-95d8-093ef809dc37	54ae4cd3-f8ba-4997-9369-bcacc6981907	\N	null	2025-11-04 20:07:28.749829+02
11b40cb3-9b77-40c8-b264-dc9f19a17cd1	1cb1b846-0ed5-46b1-95d8-093ef809dc37	8ac581ea-4236-456f-b917-c71bfda342fb	Словник	null	2025-11-04 20:07:32.617629+02
5b7b8708-7eb2-463a-a10b-0cce175e755d	1cb1b846-0ed5-46b1-95d8-093ef809dc37	57d4d112-26c3-4c36-b03a-9c671471193a	Щось там\n	null	2025-11-04 20:07:38.642652+02
d98e2825-1947-411e-9d0a-4198459a9db7	1269b91b-2fe0-4842-bb28-386ca902d07e	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-31 20:52:28.882683+02
9cbb60fc-a4da-4d70-a4e6-50ed7ca6a578	1269b91b-2fe0-4842-bb28-386ca902d07e	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-31 20:52:36.255249+02
c18d5106-e961-4080-92a9-d26847b8e137	1269b91b-2fe0-4842-bb28-386ca902d07e	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	{"3b416388-a4bc-411e-90ed-53437ec1ee16": "3b416388-a4bc-411e-90ed-53437ec1ee16", "72f2411c-3aba-400d-a5a6-a9aef91b2877": "72f2411c-3aba-400d-a5a6-a9aef91b2877", "78ab8790-b997-4486-b4f0-c49d3a66e296": "78ab8790-b997-4486-b4f0-c49d3a66e296"}	2025-10-31 20:52:53.917977+02
4efc0923-3d53-48d6-910c-353b0da45d0c	f5565c5c-9fdf-4b99-aed7-aba85403a485	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-11-01 23:49:23.1502+02
625900d9-ff5e-480d-9711-07fed02d568f	f5565c5c-9fdf-4b99-aed7-aba85403a485	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-11-01 23:49:26.087723+02
3ab7029e-6545-499e-8080-038a6e2ad79a	902cadd2-145a-4d77-92bf-d0007dab0e2b	58abd0b3-7154-41ab-939c-34012c043259	1/6	null	2025-11-04 20:25:34.767137+02
c232f4fb-9bd8-47ef-88c7-2cf5f79912fa	902cadd2-145a-4d77-92bf-d0007dab0e2b	046730fb-9825-49ab-9d88-f3f9d38fb72a	\N	null	2025-11-04 20:26:03.790512+02
340ed609-93a3-465a-83a2-065a219cb5a4	902cadd2-145a-4d77-92bf-d0007dab0e2b	866df30f-91a2-4598-aedc-8bd7b9ff7956	\N	null	2025-11-04 20:26:09.743295+02
f2e85252-6c86-49e7-bf33-123fff545c77	902cadd2-145a-4d77-92bf-d0007dab0e2b	ccdb443d-6efa-4b07-b331-bdb8ce81d640	Не знаю	null	2025-11-04 20:26:14.608155+02
13fea2ca-f236-45fd-8865-4a4e62f7f536	902cadd2-145a-4d77-92bf-d0007dab0e2b	78b592ac-107c-4ea0-b2d7-5b00fd610297	\N	{"4100d855-f5c1-49e8-885d-924a2383a24d": "4100d855-f5c1-49e8-885d-924a2383a24d", "ce7a7a90-5c25-4952-9f66-0c1802247234": "f0fa625d-ca73-4e51-9a62-3dcdd7f77378", "f0fa625d-ca73-4e51-9a62-3dcdd7f77378": "ce7a7a90-5c25-4952-9f66-0c1802247234"}	2025-11-04 20:26:30.396303+02
\.


--
-- TOC entry 5082 (class 0 OID 16670)
-- Dependencies: 232
-- Data for Name: attempts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attempts (id, exam_id, user_id, status, started_at, submitted_at, due_at, time_spent_seconds, earned_points, correct_answers, incorrect_answers, pending_count) FROM stdin;
1269b91b-2fe0-4842-bb28-386ca902d07e	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	bed7d3a1-8461-41fa-9610-03db8bc58a85	completed	2025-10-31 22:52:26.462652+02	2025-10-31 22:52:53.94434+02	2025-11-01 00:52:26.462652+02	27	100	3	0	0
f5565c5c-9fdf-4b99-aed7-aba85403a485	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	bed7d3a1-8461-41fa-9610-03db8bc58a85	completed	2025-11-02 01:49:21.812712+02	2025-11-02 01:49:33.595616+02	2025-11-02 03:49:21.812712+02	11	100	3	0	0
8eb2265f-4a06-4fc5-a751-992b6d80c439	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	bed7d3a1-8461-41fa-9610-03db8bc58a85	completed	2025-11-03 01:51:22.104994+02	2025-11-03 01:51:31.970617+02	2025-11-03 03:21:22.104994+02	9	100	3	0	0
47b8a08c-f47c-4eed-8078-aec7f18d79b9	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	2d47491e-d1e2-412d-bb81-3d8ff0174bf1	completed	2025-11-04 22:06:22.918591+02	2025-11-04 22:06:51.182667+02	2025-11-05 00:06:22.918591+02	28	100	3	0	0
1cb1b846-0ed5-46b1-95d8-093ef809dc37	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	2d47491e-d1e2-412d-bb81-3d8ff0174bf1	submitted	2025-11-04 22:07:00.668774+02	2025-11-04 22:07:38.656302+02	2025-11-05 00:07:00.668774+02	37	50	2	1	1
902cadd2-145a-4d77-92bf-d0007dab0e2b	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	ccc38203-c5e2-4924-bb5e-d754f8fc28d1	submitted	2025-11-04 22:25:30.652075+02	2025-11-04 22:26:30.426211+02	2025-11-05 00:25:30.652075+02	59	28.205128	1	3	1
\.


--
-- TOC entry 5086 (class 0 OID 16838)
-- Dependencies: 236
-- Data for Name: course_enrollments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.course_enrollments (user_id, course_id) FROM stdin;
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	f389f888-74e6-4156-90ec-b4c25e3dbb57
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	1e419816-d2fe-4908-80a1-7ae6dfd88559
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	44ea4bed-2a79-4d2a-ac13-bf425e80ba96
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	8ed0a5c0-78e3-463e-9975-b2d5053aaeba
bed7d3a1-8461-41fa-9610-03db8bc58a85	f389f888-74e6-4156-90ec-b4c25e3dbb57
bed7d3a1-8461-41fa-9610-03db8bc58a85	5e7f62e0-e724-4659-8bd8-7602561eeb54
bed7d3a1-8461-41fa-9610-03db8bc58a85	3662a170-ee7b-48d0-bb61-1261e0ce0162
bed7d3a1-8461-41fa-9610-03db8bc58a85	6dbb1528-7882-4a45-9eb0-39e9fde5f097
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	8922f9e7-1f71-4a06-93fd-270066eb5850
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	652ab3bf-a87b-49fc-825b-9139994c8b43
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	6dbb1528-7882-4a45-9eb0-39e9fde5f097
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	f389f888-74e6-4156-90ec-b4c25e3dbb57
bed7d3a1-8461-41fa-9610-03db8bc58a85	8ed0a5c0-78e3-463e-9975-b2d5053aaeba
\.


--
-- TOC entry 5078 (class 0 OID 16541)
-- Dependencies: 228
-- Data for Name: course_exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.course_exams (exam_id, course_id) FROM stdin;
a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	f389f888-74e6-4156-90ec-b4c25e3dbb57
c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	f389f888-74e6-4156-90ec-b4c25e3dbb57
b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	1e419816-d2fe-4908-80a1-7ae6dfd88559
e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	1e419816-d2fe-4908-80a1-7ae6dfd88559
a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	1e419816-d2fe-4908-80a1-7ae6dfd88559
d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	44ea4bed-2a79-4d2a-ac13-bf425e80ba96
a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	44ea4bed-2a79-4d2a-ac13-bf425e80ba96
c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	44ea4bed-2a79-4d2a-ac13-bf425e80ba96
ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	8922f9e7-1f71-4a06-93fd-270066eb5850
9dc133c5-6f45-4b7b-b930-7e938a188ff8	652ab3bf-a87b-49fc-825b-9139994c8b43
5c54d554-3551-40d2-b53f-3a00bc937287	5e7f62e0-e724-4659-8bd8-7602561eeb54
9890a2f7-0bca-4959-a005-6b1b9eeace36	3662a170-ee7b-48d0-bb61-1261e0ce0162
195e0f7b-d49f-45ee-b9d7-ad8dfb273753	6dbb1528-7882-4a45-9eb0-39e9fde5f097
3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	8ed0a5c0-78e3-463e-9975-b2d5053aaeba
\.


--
-- TOC entry 5075 (class 0 OID 16505)
-- Dependencies: 225
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (name, description, code, id, owner_id) FROM stdin;
Алгоритми та структури даних	Аналіз ефективності алгоритмів, сортування, графи.	CS201	1e419816-d2fe-4908-80a1-7ae6dfd88559	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5
Управління вимогами	Збір, аналіз та документування вимог до ПЗ.	SE401	3662a170-ee7b-48d0-bb61-1261e0ce0162	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5
Бази даних та SQL	Проектування реляційних баз даних та запити.	CS305	44ea4bed-2a79-4d2a-ac13-bf425e80ba96	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5
Патерни проектування	Вивчення класичних архітектурних рішень.	SE315	5e7f62e0-e724-4659-8bd8-7602561eeb54	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5
Чисельні методи	Наближені методи розв'язання математичних задач.	AM310	652ab3bf-a87b-49fc-825b-9139994c8b43	ccc38203-c5e2-4924-bb5e-d754f8fc28d1
Теорія ймовірностей	Основи статистичного аналізу та випадкові процеси.	AM101	6dbb1528-7882-4a45-9eb0-39e9fde5f097	ccc38203-c5e2-4924-bb5e-d754f8fc28d1
Диференціальні рівняння	Теорія та методи розв'язання диференціальних рівнянь.	AM204	8922f9e7-1f71-4a06-93fd-270066eb5850	ccc38203-c5e2-4924-bb5e-d754f8fc28d1
Вступ до QA та тестування	Принципи забезпечення якості та методи тестування ПЗ.	SE202	8ed0a5c0-78e3-463e-9975-b2d5053aaeba	ccc38203-c5e2-4924-bb5e-d754f8fc28d1
Основи програмування	Вступ до Python та структур даних.	CS101	f389f888-74e6-4156-90ec-b4c25e3dbb57	ccc38203-c5e2-4924-bb5e-d754f8fc28d1
\.


--
-- TOC entry 5077 (class 0 OID 16534)
-- Dependencies: 227
-- Data for Name: exams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.exams (id, title, instructions, start_at, end_at, max_attempts, pass_threshold, owner_id, question_count, duration_minutes) FROM stdin;
c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	Іспит з "Організації баз даних"	Дозволено користуватися власними нотатками, зробленими від руки.	2026-01-15 14:00:00+02	2026-01-15 16:00:00+02	1	70	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	120
d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	Залік з "Основ тестування програмного забезпечення"	Залік складається з тестової частини (20 питань) та практичного завдання (написання тест-кейсів).	2026-01-18 11:00:00+02	2026-01-18 13:00:00+02	3	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	120
ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	Підсумковий іспит з "Диференціальних рівнянь"	\N	2026-01-20 10:00:00+02	2026-01-20 12:00:00+02	1	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	120
e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	Іспит з "Лінійної алгебри та аналітичної геометрії"	При собі мати калькулятор. Використання мобільних телефонів заборонено.	2025-12-22 16:00:00+02	2025-12-22 18:00:00+02	1	55	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	120
9dc133c5-6f45-4b7b-b930-7e938a188ff8	Модульний контроль з "Чисельних методів"	\N	2025-12-10 14:00:00+02	2025-12-10 15:30:00+02	2	65	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	90
b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	Модульний контроль №2 з "Математичного аналізу"	\N	2025-11-25 12:00:00+02	2025-11-25 13:30:00+02	2	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	3	90
a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	Підсумковий іспит з "Алгоритми та структури даних"	Іспит складається з 30 теоретичних питань та 2 практичних завдань. Час на виконання - 120 хвилин.	2025-10-15 12:00:00+03	2025-12-20 13:00:00+02	1	65	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	4	120
5c54d554-3551-40d2-b53f-3a00bc937287	Практичний іспит з "Патернів проектування"	\N	2025-12-15 16:00:00+02	2025-12-15 18:00:00+02	1	70	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	120
195e0f7b-d49f-45ee-b9d7-ad8dfb273753	Залік з "Теорії ймовірностей"	\N	2026-01-25 09:00:00+02	2026-01-25 11:00:00+02	3	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	120
9890a2f7-0bca-4959-a005-6b1b9eeace36	Підсумковий тест з "Управління вимогами"	\N	2026-01-10 12:00:00+02	2026-01-10 13:00:00+02	1	60	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	60
3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	Тест №1 з "Основ QA"	\N	2025-11-30 10:00:00+02	2025-11-30 10:45:00+02	2	75	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	5	45
\.


--
-- TOC entry 5074 (class 0 OID 16463)
-- Dependencies: 224
-- Data for Name: login_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_history (id, user_id, login_timestamp, ip_address) FROM stdin;
\.


--
-- TOC entry 5076 (class 0 OID 16515)
-- Dependencies: 226
-- Data for Name: major_courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.major_courses (major_id, course_id) FROM stdin;
1	f389f888-74e6-4156-90ec-b4c25e3dbb57
1	1e419816-d2fe-4908-80a1-7ae6dfd88559
1	44ea4bed-2a79-4d2a-ac13-bf425e80ba96
2	8922f9e7-1f71-4a06-93fd-270066eb5850
2	652ab3bf-a87b-49fc-825b-9139994c8b43
2	6dbb1528-7882-4a45-9eb0-39e9fde5f097
3	5e7f62e0-e724-4659-8bd8-7602561eeb54
3	8ed0a5c0-78e3-463e-9975-b2d5053aaeba
3	3662a170-ee7b-48d0-bb61-1261e0ce0162
\.


--
-- TOC entry 5069 (class 0 OID 16411)
-- Dependencies: 219
-- Data for Name: majors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.majors (id, name) FROM stdin;
1	Комп'ютерні науки
2	Прикладна математика
3	Інженерія програмного забезпечення
\.


--
-- TOC entry 5081 (class 0 OID 16657)
-- Dependencies: 231
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
ce7a7a90-5c25-4952-9f66-0c1802247234	78b592ac-107c-4ea0-b2d7-5b00fd610297	Біноміальний	Кількість успіхів в серії випробувань
4100d855-f5c1-49e8-885d-924a2383a24d	78b592ac-107c-4ea0-b2d7-5b00fd610297	Пуассонівський	Кількість подій за проміжок часу
f0fa625d-ca73-4e51-9a62-3dcdd7f77378	78b592ac-107c-4ea0-b2d7-5b00fd610297	Нормальний	Симетричний, дзвоноподібний
6d32c3a5-026c-4015-b1a3-883890cfc0f3	34cc42bd-ae84-4e63-98e1-3be2ea6454d6	Модульне	Тестування окремих функцій
b1795d16-96b3-4e2d-b916-c407d4230b5d	34cc42bd-ae84-4e63-98e1-3be2ea6454d6	Інтеграційне	Тестування взаємодії модулів
77051630-be9c-4230-aafe-8628cec4eb23	34cc42bd-ae84-4e63-98e1-3be2ea6454d6	Системне	Тестування всієї системи
\.


--
-- TOC entry 5080 (class 0 OID 16643)
-- Dependencies: 230
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
e26069f9-1edf-4e94-9c25-84cac8068d3d	58abd0b3-7154-41ab-939c-34012c043259	1/6	t
e34ecc8b-d4eb-4d22-a876-a3bdaf612e7f	046730fb-9825-49ab-9d88-f3f9d38fb72a	Зріст людини	t
115f6482-53d7-46c8-8c47-8129acdca288	046730fb-9825-49ab-9d88-f3f9d38fb72a	Кількість студентів в аудиторії	f
a0ea1c6d-989a-43ae-80cf-956a27921b7c	046730fb-9825-49ab-9d88-f3f9d38fb72a	Час очікування автобуса	t
02db3b4e-f775-4b46-9fa5-39a2ecc941e8	046730fb-9825-49ab-9d88-f3f9d38fb72a	Кількість опадів	t
309c89b1-ad92-4d43-a02f-cea8f446b542	866df30f-91a2-4598-aedc-8bd7b9ff7956	Розкид значень	f
6681d839-c86b-4c3a-b62e-642f542016b7	866df30f-91a2-4598-aedc-8bd7b9ff7956	Середнє очікуване значення	t
4502a8ec-3f69-47d0-b855-83ad19b26a79	866df30f-91a2-4598-aedc-8bd7b9ff7956	Найбільш часте значення	f
aa501b05-1206-491a-a331-b3db6619d61d	e124ab1c-fb8f-4322-9c16-16c469b4273b	Функціональне	f
8eb046f2-11c5-463d-a861-4b0e5a30bf8d	e124ab1c-fb8f-4322-9c16-16c469b4273b	Регресійне	t
a2c339c1-00d2-4b0b-9c37-0eebd506283b	e124ab1c-fb8f-4322-9c16-16c469b4273b	Навантажувальне	f
917b93cf-fe32-4d00-a7d1-8de6607b0b14	04ef602c-452b-4150-9ee7-5d236d67b73f	Вичерпне тестування неможливе	t
ebc4c6ce-612f-431b-b73c-32f2f2eda367	04ef602c-452b-4150-9ee7-5d236d67b73f	Тестування показує наявність дефектів	t
42b7c579-4cfe-45c9-be51-10b759d7af62	04ef602c-452b-4150-9ee7-5d236d67b73f	Раннє тестування економить час	t
d4b2f13c-c021-42b0-a8c0-d840799112cd	04ef602c-452b-4150-9ee7-5d236d67b73f	Тестування має проводитись лише в кінці	f
79d084bd-9c99-435e-935e-5ebed0e2c2fc	133daafb-e076-45a8-9a18-a51128eb4548	Тест-кейс	t
9ec77b4c-0679-4897-b8bb-81bc5f739077	133daafb-e076-45a8-9a18-a51128eb4548	Test Case	t
\.


--
-- TOC entry 5085 (class 0 OID 16723)
-- Dependencies: 235
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
-- TOC entry 5079 (class 0 OID 16629)
-- Dependencies: 229
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (id, exam_id, question_type, title, "position", points) FROM stdin;
54ae4cd3-f8ba-4997-9369-bcacc6981907	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	multi_choice	Які з наведених структур даних працюють за принципом LIFO (Last-In, First-Out)?	2	2
3696e8f2-4e53-40de-9d85-8d558857567d	9dc133c5-6f45-4b7b-b930-7e938a188ff8	long_answer	Опишіть суть методу Рунге-Кутти 4-го порядку.	2	5
913f9e2b-a6f4-44e7-9093-3f7f6d90d047	9dc133c5-6f45-4b7b-b930-7e938a188ff8	short_answer	Що таке інтерполяція?	3	2
4afb6046-c19e-42f4-b446-3b8930400063	9dc133c5-6f45-4b7b-b930-7e938a188ff8	multi_choice	Які методи використовуються для розв'язання СЛАР?	4	2
608774c5-de82-4170-b682-ae0247e6cef3	9dc133c5-6f45-4b7b-b930-7e938a188ff8	single_choice	Що є основною ідеєю методу Монте-Карло?	5	1
47400ebe-b66d-4dd8-bf62-53ae188905ef	5c54d554-3551-40d2-b53f-3a00bc937287	matching	Встановіть відповідність між патерном та його типом (Твірний, Структурний, Поведінковий).	1	3
2dea9796-ad9f-48ef-bf46-efa103180102	5c54d554-3551-40d2-b53f-3a00bc937287	single_choice	Який патерн забезпечує існування лише одного екземпляра класу?	2	1
57d4d112-26c3-4c36-b03a-9c671471193a	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	long_answer	Поясніть своїми словами різницю між масивом (Array) та зв'язаним списком (Linked List), вказавши переваги та недоліки кожного.	4	5
bfa9c358-36ae-4299-a1de-aefc16ddbfc3	5c54d554-3551-40d2-b53f-3a00bc937287	multi_choice	Які патерни належать до "банди чотирьох" (GoF)?	3	2
292f04a8-5cf8-44b8-bc40-36c68437dfd9	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	matching	Встановіть відповідність між рівнем тестування та його описом.	3	3
96d6d933-b40e-4189-bc7f-4af3bc3c5d3b	5c54d554-3551-40d2-b53f-3a00bc937287	short_answer	Як називається патерн, що дозволяє об'єктам змінювати свою поведінку, коли їхній внутрішній стан змінюється?	4	2
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
3deddb21-28be-4ea5-a5ca-f3b14896ff32	ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	single_choice	Якого порядку рівняння y'' + 2y' - y = 0?	1	1
aec7e638-c795-4d63-8c85-d7e63cc57a6f	ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	short_answer	Знайдіть загальний розв'язок рівняння y' = cos(x).	2	2
1f117166-b0b8-4d79-9a86-c46c5ca80dd9	ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	multi_choice	Які з цих рівнянь є лінійними?	3	2
d890e059-8068-4c71-8d5f-e28ff3fb1a69	ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	long_answer	Опишіть метод варіації довільної сталої.	4	5
6f379cd8-5bca-45e0-b6c4-7c6e45af795c	5c54d554-3551-40d2-b53f-3a00bc937287	long_answer	Опишіть патерн "Спостерігач" (Observer) та наведіть приклад його використання.	5	5
2b45040c-4f4f-4851-bf1e-a2b13fd9cea6	ab1841d6-2f5a-4cf1-8833-f2dd63ed23dd	matching	Встановіть відповідність між типом рівняння та його прикладом.	5	3
cbf75a65-3cba-48db-8320-bfa9accbea4c	9dc133c5-6f45-4b7b-b930-7e938a188ff8	single_choice	Який метод використовується для чисельного інтегрування?	1	1
85105a55-4047-4318-844f-58edc6cdccc9	9890a2f7-0bca-4959-a005-6b1b9eeace36	long_answer	Що таке функціональні та нефункціональні вимоги? Наведіть приклади.	1	5
fe70f07d-c62d-4950-b6d2-8dcebaaf2635	9890a2f7-0bca-4959-a005-6b1b9eeace36	single_choice	Який документ є основним результатом етапу збору вимог?	2	1
68c7f4a8-28e0-4b6f-ba10-4b5c225ce096	9890a2f7-0bca-4959-a005-6b1b9eeace36	short_answer	Як розшифровується акронім SRS?	3	2
4574e52c-b6ad-416f-9818-7fb8d6b7dac5	9890a2f7-0bca-4959-a005-6b1b9eeace36	multi_choice	Які атрибути якості має мати хороша вимога (за стандартом ISO)?	4	2
df041048-9815-492c-913c-9fe10902f6a7	9890a2f7-0bca-4959-a005-6b1b9eeace36	matching	Зіставте техніку виявлення вимог з її описом.	5	3
58abd0b3-7154-41ab-939c-34012c043259	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	short_answer	Яка ймовірність випадання "шістки" при одному киданні грального кубика? (Відповідь у форматі 1/6)	1	2
046730fb-9825-49ab-9d88-f3f9d38fb72a	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	multi_choice	Оберіть неперервні випадкові величини.	2	2
866df30f-91a2-4598-aedc-8bd7b9ff7956	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	single_choice	Що вимірює математичне сподівання?	3	1
ccdb443d-6efa-4b07-b331-bdb8ce81d640	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	long_answer	Сформулюйте центральну граничну теорему.	4	5
78b592ac-107c-4ea0-b2d7-5b00fd610297	195e0f7b-d49f-45ee-b9d7-ad8dfb273753	matching	Зіставте назву розподілу з його властивістю.	5	3
e124ab1c-fb8f-4322-9c16-16c469b4273b	3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	single_choice	Який вид тестування виконується для перевірки, що нові зміни не зламали існуючий функціонал?	1	1
04ef602c-452b-4150-9ee7-5d236d67b73f	3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	multi_choice	Що з переліченого є принципами тестування?	2	2
133daafb-e076-45a8-9a18-a51128eb4548	3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	short_answer	Як називається документ, що описує кроки для перевірки певної функціональності?	3	2
ab71f0ea-ac4c-4e3a-ae16-afa357f5b324	3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	long_answer	Опишіть різницю між чорно-скриньковим та біло-скриньковим тестуванням.	4	5
34cc42bd-ae84-4e63-98e1-3be2ea6454d6	3b5b9f6b-8aa3-4e4a-88f0-21ca6e949ee6	matching	Встановіть відповідність між рівнем тестування та його метою.	5	3
\.


--
-- TOC entry 5067 (class 0 OID 16400)
-- Dependencies: 217
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name) FROM stdin;
1	student
2	teacher
3	supervisor
\.


--
-- TOC entry 5072 (class 0 OID 16447)
-- Dependencies: 222
-- Data for Name: user_majors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_majors (user_id, major_id) FROM stdin;
bed7d3a1-8461-41fa-9610-03db8bc58a85	3
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	1
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	2
\.


--
-- TOC entry 5071 (class 0 OID 16432)
-- Dependencies: 221
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_roles (user_id, role_id) FROM stdin;
bed7d3a1-8461-41fa-9610-03db8bc58a85	1
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	1
a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	2
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	1
\.


--
-- TOC entry 5070 (class 0 OID 16421)
-- Dependencies: 220
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, created_at, first_name, last_name, patronymic, notification_settings, avatar_url) FROM stdin;
bed7d3a1-8461-41fa-9610-03db8bc58a85	chulano10@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:14:50.302061+03	Владислава	Колінько	Володимирівна	{"enabled": true, "remind_before_hours": [1, 8, 24]}	https://res.cloudinary.com/dsiiuchan/image/upload/v1761943437/user_avatars/bed7d3a1-8461-41fa-9610-03db8bc58a85.jpg
2d47491e-d1e2-412d-bb81-3d8ff0174bf1	miroslava.flom@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:15:27.673607+03	Мирослава	Фломбойм	Олексіївна	{"enabled": false, "remind_before_hours": []}	\N
ccc38203-c5e2-4924-bb5e-d754f8fc28d1	anastasiabakalyna@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:15:06.219423+03	Анастасія	Бакалина	Ярославівна	{"enabled": false, "remind_before_hours": []}	\N
a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	minelenova1@gmail.com	$2b$12$7x2y/2LaaJBSaeAanKdGeuo4XVl3k0qXaVPAdbtVmcPDjkjh79kdy	2025-10-10 18:01:19.539414+03	Олександра	Малій	Михайлівна	{"enabled": false, "remind_before_hours": []}	https://res.cloudinary.com/dsiiuchan/image/upload/v1761943285/user_avatars/a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5.jpg
\.


--
-- TOC entry 5096 (class 0 OID 0)
-- Dependencies: 223
-- Name: login_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.login_history_id_seq', 1, false);


--
-- TOC entry 5097 (class 0 OID 0)
-- Dependencies: 218
-- Name: majors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.majors_id_seq', 4, true);


--
-- TOC entry 5098 (class 0 OID 0)
-- Dependencies: 216
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_seq', 8, true);


--
-- TOC entry 4899 (class 2606 OID 16921)
-- Name: course_enrollments course_enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT course_enrollments_pkey PRIMARY KEY (user_id, course_id);


--
-- TOC entry 4875 (class 2606 OID 16928)
-- Name: course_exams course_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_pkey PRIMARY KEY (exam_id, course_id);


--
-- TOC entry 4869 (class 2606 OID 16514)
-- Name: courses courses_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_code_key UNIQUE (code);


--
-- TOC entry 4871 (class 2606 OID 16902)
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- TOC entry 4886 (class 2606 OID 16676)
-- Name: attempts exam_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT exam_attempts_pkey PRIMARY KEY (id);


--
-- TOC entry 4873 (class 2606 OID 16540)
-- Name: exams exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exams
    ADD CONSTRAINT exams_pkey PRIMARY KEY (id);


--
-- TOC entry 4867 (class 2606 OID 16471)
-- Name: login_history login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4855 (class 2606 OID 16420)
-- Name: majors majors_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_name_key UNIQUE (name);


--
-- TOC entry 4857 (class 2606 OID 16418)
-- Name: majors majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_pkey PRIMARY KEY (id);


--
-- TOC entry 4884 (class 2606 OID 16664)
-- Name: matching_pairs matching_pairs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_pairs
    ADD CONSTRAINT matching_pairs_pkey PRIMARY KEY (id);


--
-- TOC entry 4881 (class 2606 OID 16651)
-- Name: options options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.options
    ADD CONSTRAINT options_pkey PRIMARY KEY (id);


--
-- TOC entry 4897 (class 2606 OID 16728)
-- Name: question_type_weights question_type_weights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.question_type_weights
    ADD CONSTRAINT question_type_weights_pkey PRIMARY KEY (question_type);


--
-- TOC entry 4878 (class 2606 OID 16637)
-- Name: questions questions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_pkey PRIMARY KEY (id);


--
-- TOC entry 4851 (class 2606 OID 16409)
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 4853 (class 2606 OID 16407)
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- TOC entry 4895 (class 2606 OID 16706)
-- Name: answer_options student_answer_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_pkey PRIMARY KEY (answer_id, selected_option_id);


--
-- TOC entry 4891 (class 2606 OID 16691)
-- Name: answers student_answers_attempt_id_question_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_attempt_id_question_id_key UNIQUE (attempt_id, question_id);


--
-- TOC entry 4893 (class 2606 OID 16689)
-- Name: answers student_answers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_pkey PRIMARY KEY (id);


--
-- TOC entry 4865 (class 2606 OID 16451)
-- Name: user_majors user_majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4863 (class 2606 OID 16436)
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- TOC entry 4859 (class 2606 OID 16431)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4861 (class 2606 OID 16429)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- TOC entry 4887 (class 1259 OID 16721)
-- Name: idx_exam_attempts_on_exam_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_attempts_on_exam_id ON public.attempts USING btree (exam_id);


--
-- TOC entry 4888 (class 1259 OID 16720)
-- Name: idx_exam_attempts_on_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exam_attempts_on_user_id ON public.attempts USING btree (user_id);


--
-- TOC entry 4882 (class 1259 OID 16719)
-- Name: idx_matching_pairs_on_question_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matching_pairs_on_question_id ON public.matching_pairs USING btree (question_id);


--
-- TOC entry 4879 (class 1259 OID 16718)
-- Name: idx_options_on_question_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_options_on_question_id ON public.options USING btree (question_id);


--
-- TOC entry 4876 (class 1259 OID 16717)
-- Name: idx_questions_on_exam_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_questions_on_exam_id ON public.questions USING btree (exam_id);


--
-- TOC entry 4889 (class 1259 OID 16722)
-- Name: idx_student_answers_on_attempt_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_student_answers_on_attempt_id ON public.answers USING btree (attempt_id);


--
-- TOC entry 4920 (class 2620 OID 16731)
-- Name: questions questions_count_update_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_count_update_trigger AFTER INSERT OR DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.update_exam_question_count_trigger();


--
-- TOC entry 4921 (class 2620 OID 16735)
-- Name: questions questions_reorder_after_delete; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_reorder_after_delete AFTER DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.reorder_questions_on_delete();


--
-- TOC entry 4922 (class 2620 OID 16733)
-- Name: questions questions_set_position_before_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_set_position_before_insert BEFORE INSERT ON public.questions FOR EACH ROW EXECUTE FUNCTION public.set_question_position_on_insert();


--
-- TOC entry 4918 (class 2606 OID 16851)
-- Name: course_enrollments course_enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT course_enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4908 (class 2606 OID 16551)
-- Name: course_exams course_exams_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4905 (class 2606 OID 16922)
-- Name: courses courses_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);


--
-- TOC entry 4913 (class 2606 OID 16677)
-- Name: attempts exam_attempts_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT exam_attempts_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4919 (class 2606 OID 16903)
-- Name: course_enrollments fk_course_enrollments_course_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_enrollments
    ADD CONSTRAINT fk_course_enrollments_course_id FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4909 (class 2606 OID 16908)
-- Name: course_exams fk_course_exams_course_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT fk_course_exams_course_id FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4906 (class 2606 OID 16913)
-- Name: major_courses fk_major_courses_course_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT fk_major_courses_course_id FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4904 (class 2606 OID 16472)
-- Name: login_history login_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4907 (class 2606 OID 16520)
-- Name: major_courses major_courses_major_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.majors(id) ON DELETE CASCADE;


--
-- TOC entry 4912 (class 2606 OID 16665)
-- Name: matching_pairs matching_pairs_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_pairs
    ADD CONSTRAINT matching_pairs_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4911 (class 2606 OID 16652)
-- Name: options options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.options
    ADD CONSTRAINT options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4910 (class 2606 OID 16638)
-- Name: questions questions_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4916 (class 2606 OID 16712)
-- Name: answer_options student_answer_options_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.options(id) ON DELETE CASCADE;


--
-- TOC entry 4917 (class 2606 OID 16707)
-- Name: answer_options student_answer_options_student_answer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_student_answer_id_fkey FOREIGN KEY (answer_id) REFERENCES public.answers(id) ON DELETE CASCADE;


--
-- TOC entry 4914 (class 2606 OID 16692)
-- Name: answers student_answers_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.attempts(id) ON DELETE CASCADE;


--
-- TOC entry 4915 (class 2606 OID 16697)
-- Name: answers student_answers_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4902 (class 2606 OID 16457)
-- Name: user_majors user_majors_major_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.majors(id) ON DELETE RESTRICT;


--
-- TOC entry 4903 (class 2606 OID 16452)
-- Name: user_majors user_majors_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4900 (class 2606 OID 16442)
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE RESTRICT;


--
-- TOC entry 4901 (class 2606 OID 16437)
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


-- Completed on 2025-11-04 23:02:11

--
-- PostgreSQL database dump complete
--

\unrestrict 3pXITESzWB9cubE6jWqg5hq6euBMg8j7Reh68vT7QPeEA2Kpcg4xFxUWpuznJLP

