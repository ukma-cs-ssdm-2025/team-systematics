--
-- PostgreSQL database dump
--

\restrict 5fmbcsL1gOKOciiYLbAeZzgQmKFx6FE7ndd9OySb2LCpBaXUPiRnGGHyTbmBSXt

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

-- Started on 2025-10-20 20:32:25

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
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- TOC entry 905 (class 1247 OID 16610)
-- Name: attempt_status_enum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attempt_status_enum AS ENUM (
    'in_progress',
    'submitted',
    'completed'
);


ALTER TYPE public.attempt_status_enum OWNER TO postgres;

--
-- TOC entry 926 (class 1247 OID 16748)
-- Name: attemptstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attemptstatus AS ENUM (
    'in_progress',
    'submitted',
    'expired'
);


ALTER TYPE public.attemptstatus OWNER TO postgres;

--
-- TOC entry 908 (class 1247 OID 16618)
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
-- TOC entry 923 (class 1247 OID 16737)
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
-- TOC entry 250 (class 1255 OID 16734)
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
-- TOC entry 249 (class 1255 OID 16732)
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
-- TOC entry 248 (class 1255 OID 16730)
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
    score_percent integer,
    started_at timestamp with time zone NOT NULL,
    submitted_at timestamp with time zone,
    due_at timestamp with time zone NOT NULL
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
-- TOC entry 5091 (class 0 OID 0)
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
-- TOC entry 5092 (class 0 OID 0)
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
-- TOC entry 5093 (class 0 OID 0)
-- Dependencies: 218
-- Name: majors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.majors_id_seq OWNED BY public.majors.id;


--
-- TOC entry 237 (class 1259 OID 16811)
-- Name: matching_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matching_data (
    id uuid NOT NULL,
    question_id uuid NOT NULL,
    prompt text NOT NULL,
    correct_match text NOT NULL
);


ALTER TABLE public.matching_data OWNER TO postgres;

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
    points integer DEFAULT 1 NOT NULL
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
-- TOC entry 5094 (class 0 OID 0)
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
-- TOC entry 4838 (class 2604 OID 16508)
-- Name: courses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses ALTER COLUMN id SET DEFAULT nextval('public.courses_id_seq'::regclass);


--
-- TOC entry 4836 (class 2604 OID 16466)
-- Name: login_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history ALTER COLUMN id SET DEFAULT nextval('public.login_history_id_seq'::regclass);


--
-- TOC entry 4833 (class 2604 OID 16414)
-- Name: majors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors ALTER COLUMN id SET DEFAULT nextval('public.majors_id_seq'::regclass);


--
-- TOC entry 4832 (class 2604 OID 16403)
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- TOC entry 5082 (class 0 OID 16702)
-- Dependencies: 235
-- Data for Name: answer_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answer_options (answer_id, selected_option_id) FROM stdin;
64adf431-5f8a-4962-b477-067c766286cb	b157b137-bcf2-45c2-a63e-512ad657e7aa
01f4d07a-e416-4203-b380-2e5d40ccd4bf	d9757a3e-bdb3-4ac4-9b27-f842691931f0
01f4d07a-e416-4203-b380-2e5d40ccd4bf	b5d07d28-d5e5-4bd3-ba22-65771cbe028b
a53c269a-8642-425b-9bd2-e2c86063af61	557d6fc8-6f8d-45ab-aa4a-faecdfef71f7
cc63ebdb-8309-4220-ac3f-7069fe79dd5d	b2f8ce79-2ef7-4f08-b070-1868211a3de0
cc63ebdb-8309-4220-ac3f-7069fe79dd5d	3b896b82-3d69-460f-82dd-e89855b7526f
1ca8acab-77f6-42cd-b25f-5fdcbb771f19	557d6fc8-6f8d-45ab-aa4a-faecdfef71f7
cd433f25-42ab-4db9-be28-47acd07d011d	3b896b82-3d69-460f-82dd-e89855b7526f
cd433f25-42ab-4db9-be28-47acd07d011d	e149dd3e-086e-4b1c-8463-79ff8227adf7
1b87d557-c4fb-41c2-85e6-97e47d2e2f39	b157b137-bcf2-45c2-a63e-512ad657e7aa
0024f349-121d-4a36-b42c-a3fda6f5608e	d9757a3e-bdb3-4ac4-9b27-f842691931f0
0024f349-121d-4a36-b42c-a3fda6f5608e	b5d07d28-d5e5-4bd3-ba22-65771cbe028b
ebcf3416-497b-46c1-adf1-4acb88f3113f	deea8e65-a1ae-4374-b6f3-2cb3a14db7f4
8edaf5a8-d829-4a81-b6cc-5c29bae138ac	3b896b82-3d69-460f-82dd-e89855b7526f
8edaf5a8-d829-4a81-b6cc-5c29bae138ac	e149dd3e-086e-4b1c-8463-79ff8227adf7
db2adf76-4f3b-4ad4-83ed-c1fb91065495	c23081f2-b9f5-4b2b-b084-64f57eb45bb6
52e5eb4b-5d85-48cc-b2f6-dfbdbcc1bc4c	8b24c98e-3a1e-438c-b7c4-f6f91a8b7d1b
52e5eb4b-5d85-48cc-b2f6-dfbdbcc1bc4c	7f8dfce9-cbb3-4a77-bea2-72b7484fc637
73857022-9872-46e6-9af5-5fe9876fca1b	557d6fc8-6f8d-45ab-aa4a-faecdfef71f7
b7b0bfb2-8119-42c9-8129-1e81eca8a400	b2f8ce79-2ef7-4f08-b070-1868211a3de0
b7b0bfb2-8119-42c9-8129-1e81eca8a400	3b896b82-3d69-460f-82dd-e89855b7526f
863eaebb-3f61-40e1-8f43-4b25fc26a5f6	b157b137-bcf2-45c2-a63e-512ad657e7aa
80d9e13f-0f0a-4adc-be1e-9b1aa18518ed	d9757a3e-bdb3-4ac4-9b27-f842691931f0
80d9e13f-0f0a-4adc-be1e-9b1aa18518ed	b5d07d28-d5e5-4bd3-ba22-65771cbe028b
9b3171fc-1cae-47b1-8167-009c3f47dca7	b157b137-bcf2-45c2-a63e-512ad657e7aa
1fe1cd0d-8c62-4bf9-acec-80d9bc1c70c6	d9757a3e-bdb3-4ac4-9b27-f842691931f0
1c9f6f60-403a-4523-b438-21b1c36055d0	557d6fc8-6f8d-45ab-aa4a-faecdfef71f7
aebb4ccd-27e1-458a-a2be-661a91614d37	e149dd3e-086e-4b1c-8463-79ff8227adf7
aebb4ccd-27e1-458a-a2be-661a91614d37	3b896b82-3d69-460f-82dd-e89855b7526f
40d2d544-bae8-472a-b14b-8ffdc29b50f0	1af47804-e5e6-4f3f-a807-6fccbc5b1d55
c2afcf61-db94-4c45-bab6-49cb3d504e71	bc65a758-5552-4d1b-a978-3824383c7118
0563e507-7e64-48d3-a207-4ee2e9a048a9	c23081f2-b9f5-4b2b-b084-64f57eb45bb6
63f33471-0cc8-4434-b326-7fa531bba037	cabea420-6eb2-44c4-93a4-cc463e95b315
e39f2860-b21f-4551-bca3-e5936769f2cb	4006f586-0fe5-47a5-a21b-38a037a72ec6
09ef45a2-4869-4c47-9ba9-36dc72c0991e	d9757a3e-bdb3-4ac4-9b27-f842691931f0
09ef45a2-4869-4c47-9ba9-36dc72c0991e	b5d07d28-d5e5-4bd3-ba22-65771cbe028b
\.


--
-- TOC entry 5081 (class 0 OID 16682)
-- Dependencies: 234
-- Data for Name: answers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.answers (id, attempt_id, question_id, answer_text, answer_json, saved_at) FROM stdin;
73857022-9872-46e6-9af5-5fe9876fca1b	85c23a7b-c67d-4926-8671-93eb18c65542	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	null	2025-10-20 17:07:19.841791+03
b7b0bfb2-8119-42c9-8129-1e81eca8a400	85c23a7b-c67d-4926-8671-93eb18c65542	a599186c-5893-4137-ada0-3aa79fd902ee	\N	null	2025-10-20 17:07:22.416342+03
72c6f0ce-0698-472e-91b1-8f238e56a484	863af9e0-b0bb-428e-b507-e3faba85abca	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	{"selected_option_ids": ["557d6fc8-6f8d-45ab-aa4a-faecdfef71f7"]}	2025-10-20 02:16:30.014116+03
9726791a-2453-448e-9d51-294d0f8cb025	863af9e0-b0bb-428e-b507-e3faba85abca	a599186c-5893-4137-ada0-3aa79fd902ee	\N	{"selected_option_ids": ["3b896b82-3d69-460f-82dd-e89855b7526f", "e149dd3e-086e-4b1c-8463-79ff8227adf7"]}	2025-10-20 02:17:53.112059+03
7a6e9e4f-e58f-42dc-bafe-4454e70bda2d	863af9e0-b0bb-428e-b507-e3faba85abca	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	Testing	{"selected_option_ids": null}	2025-10-20 02:18:16.670314+03
cf2a6eb4-a979-4d2a-9d92-541c1cb12e1e	82da63f3-e163-41ba-b6ab-d080cbc30fc6	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	{"selected_option_ids": ["deea8e65-a1ae-4374-b6f3-2cb3a14db7f4"]}	2025-10-20 02:22:40.034356+03
4f03088b-a989-4f71-b0db-d231984ea1ce	82da63f3-e163-41ba-b6ab-d080cbc30fc6	a599186c-5893-4137-ada0-3aa79fd902ee	\N	{"selected_option_ids": ["3b896b82-3d69-460f-82dd-e89855b7526f"]}	2025-10-20 02:22:41.151084+03
d449dc8a-7297-4757-92bb-4d3ba5c11f4a	82da63f3-e163-41ba-b6ab-d080cbc30fc6	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	Testing2	{"selected_option_ids": null}	2025-10-20 02:22:48.398615+03
64adf431-5f8a-4962-b477-067c766286cb	85bdf016-c9a7-4ef5-8598-b6dbef9b627b	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-20 02:46:55.822846+03
01f4d07a-e416-4203-b380-2e5d40ccd4bf	85bdf016-c9a7-4ef5-8598-b6dbef9b627b	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-20 02:47:28.212146+03
5651a69f-ddae-432a-a99c-6fa87af25dcf	85bdf016-c9a7-4ef5-8598-b6dbef9b627b	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	\N	2025-10-20 02:47:31.24744+03
a53c269a-8642-425b-9bd2-e2c86063af61	5fd6898a-826a-4598-9a1d-02e27bab7bd4	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	null	2025-10-20 02:47:42.077355+03
cc63ebdb-8309-4220-ac3f-7069fe79dd5d	5fd6898a-826a-4598-9a1d-02e27bab7bd4	a599186c-5893-4137-ada0-3aa79fd902ee	\N	null	2025-10-20 02:47:43.332267+03
b6c4c157-8bed-4846-ba8a-d25493939532	5fd6898a-826a-4598-9a1d-02e27bab7bd4	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	lol\n	null	2025-10-20 02:47:47.593263+03
1ca8acab-77f6-42cd-b25f-5fdcbb771f19	0d8b7fed-f5ee-4fee-ad7d-b97724c68a43	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	null	2025-10-20 13:21:21.090502+03
cd433f25-42ab-4db9-be28-47acd07d011d	0d8b7fed-f5ee-4fee-ad7d-b97724c68a43	a599186c-5893-4137-ada0-3aa79fd902ee	\N	null	2025-10-20 13:21:22.23971+03
12d21aa9-c177-404f-a7eb-464ce10384ea	85c23a7b-c67d-4926-8671-93eb18c65542	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	А я не знаю	null	2025-10-20 17:07:29.814572+03
eba5a5c6-9aba-4f7d-a2ca-0a00bb7faf62	0d8b7fed-f5ee-4fee-ad7d-b97724c68a43	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	Lol	null	2025-10-20 13:21:24.77904+03
1b87d557-c4fb-41c2-85e6-97e47d2e2f39	01dcb31d-7198-47ee-85f5-60e295efb9a7	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-20 13:22:33.102213+03
0024f349-121d-4a36-b42c-a3fda6f5608e	01dcb31d-7198-47ee-85f5-60e295efb9a7	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-20 13:22:34.462783+03
02343d48-d7f0-4329-a271-619ed9fbce56	01dcb31d-7198-47ee-85f5-60e295efb9a7	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	\N	2025-10-20 13:22:35.473888+03
ebcf3416-497b-46c1-adf1-4acb88f3113f	2993a9a7-f9dc-4cac-8714-94e7879a98f7	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	null	2025-10-20 13:23:51.228001+03
8edaf5a8-d829-4a81-b6cc-5c29bae138ac	2993a9a7-f9dc-4cac-8714-94e7879a98f7	a599186c-5893-4137-ada0-3aa79fd902ee	\N	null	2025-10-20 13:23:52.544329+03
5840976f-21a4-420c-8684-450a1f2090a6	2993a9a7-f9dc-4cac-8714-94e7879a98f7	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	Hey	null	2025-10-20 13:23:55.097958+03
db2adf76-4f3b-4ad4-83ed-c1fb91065495	9195d614-3654-42d3-b6c4-38360237206c	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	\N	null	2025-10-20 13:24:06.830704+03
52e5eb4b-5d85-48cc-b2f6-dfbdbcc1bc4c	9195d614-3654-42d3-b6c4-38360237206c	8e45a053-35f9-4c82-a9ad-dfa4fac62137	\N	null	2025-10-20 13:24:07.678135+03
4ab34514-f048-4dfc-80c5-36f9cff625b7	9195d614-3654-42d3-b6c4-38360237206c	0b6926df-8c4e-413f-a7ee-66cd7b4de6b8	2	null	2025-10-20 13:24:08.770707+03
79f94838-8c14-49cc-bd8e-bfb8542e02cd	9195d614-3654-42d3-b6c4-38360237206c	86eb5e7f-2889-417c-84b7-4833fb7656e7	232	null	2025-10-20 13:24:09.901879+03
87b0bd48-c7ce-4e00-8b5c-c2e46bfe92f9	9195d614-3654-42d3-b6c4-38360237206c	b5130cc8-1837-4715-9749-68b879fd5f5d	\N	\N	2025-10-20 13:24:10.555507+03
863eaebb-3f61-40e1-8f43-4b25fc26a5f6	a8db8cfb-a0c4-4c91-944e-a4a97e9430a3	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-20 17:08:16.967999+03
80d9e13f-0f0a-4adc-be1e-9b1aa18518ed	a8db8cfb-a0c4-4c91-944e-a4a97e9430a3	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-20 17:08:17.96912+03
f8bf5b07-ff36-4bf5-b3ca-148fa94e8e70	a8db8cfb-a0c4-4c91-944e-a4a97e9430a3	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	\N	2025-10-20 17:08:18.783485+03
9b3171fc-1cae-47b1-8167-009c3f47dca7	df518ada-634a-4d43-82bb-3d3536ba6123	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-20 17:10:37.854274+03
1fe1cd0d-8c62-4bf9-acec-80d9bc1c70c6	df518ada-634a-4d43-82bb-3d3536ba6123	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-20 17:10:39.138662+03
c7eb1d56-2cf0-4483-8eea-e6c42b93e8eb	df518ada-634a-4d43-82bb-3d3536ba6123	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	\N	2025-10-20 17:10:40.076508+03
1c9f6f60-403a-4523-b438-21b1c36055d0	43222e87-bbd5-429a-88ca-0b21423f2c51	e9c4b680-8443-43e0-b05e-e8a56f61d40d	\N	null	2025-10-20 17:20:09.863063+03
aebb4ccd-27e1-458a-a2be-661a91614d37	43222e87-bbd5-429a-88ca-0b21423f2c51	a599186c-5893-4137-ada0-3aa79fd902ee	\N	null	2025-10-20 17:20:11.381975+03
09ef45a2-4869-4c47-9ba9-36dc72c0991e	7619423d-cb07-4381-8914-6eea36967d01	32ea01f5-33ec-4ff8-891a-b48349f9078a	\N	null	2025-10-20 17:26:12.905826+03
67452570-3d29-48f6-b808-320065f02419	43222e87-bbd5-429a-88ca-0b21423f2c51	732eb6fb-2faf-41ee-979f-c7e0aa2d454f	34	null	2025-10-20 17:20:12.826845+03
40d2d544-bae8-472a-b14b-8ffdc29b50f0	5796b076-78aa-4904-aae7-0eafefd727d0	c66488df-9d33-4e77-aab6-320762a544eb	\N	null	2025-10-20 17:20:37.777186+03
c2afcf61-db94-4c45-bab6-49cb3d504e71	5796b076-78aa-4904-aae7-0eafefd727d0	54ae4cd3-f8ba-4997-9369-bcacc6981907	\N	null	2025-10-20 17:20:38.714281+03
3527cb25-ab5e-450f-bb9f-46ae5cf68fab	5796b076-78aa-4904-aae7-0eafefd727d0	8ac581ea-4236-456f-b917-c71bfda342fb	Хз	null	2025-10-20 17:20:42.253561+03
ec7e786a-43af-41ad-8061-b89524028a51	5796b076-78aa-4904-aae7-0eafefd727d0	57d4d112-26c3-4c36-b03a-9c671471193a	Ой	null	2025-10-20 17:20:44.52697+03
0563e507-7e64-48d3-a207-4ee2e9a048a9	de19e64f-6fb5-4110-875a-a4ce39cd5e08	16e8b1f9-af8f-4b56-9bbd-d65d6a658526	\N	null	2025-10-20 17:22:24.450165+03
63f33471-0cc8-4434-b326-7fa531bba037	de19e64f-6fb5-4110-875a-a4ce39cd5e08	8e45a053-35f9-4c82-a9ad-dfa4fac62137	\N	null	2025-10-20 17:22:25.566963+03
1ae0b488-45da-4f4a-987a-b9f87c331b82	de19e64f-6fb5-4110-875a-a4ce39cd5e08	0b6926df-8c4e-413f-a7ee-66cd7b4de6b8	4	null	2025-10-20 17:22:28.143008+03
f721e7f7-03dc-4ace-b368-15f768fa86d0	de19e64f-6fb5-4110-875a-a4ce39cd5e08	86eb5e7f-2889-417c-84b7-4833fb7656e7	l	null	2025-10-20 17:22:30.666725+03
3cb5fbfc-f7ea-41ea-a83c-4557dcce02e2	de19e64f-6fb5-4110-875a-a4ce39cd5e08	b5130cc8-1837-4715-9749-68b879fd5f5d	\N	\N	2025-10-20 17:22:31.486329+03
e39f2860-b21f-4551-bca3-e5936769f2cb	7619423d-cb07-4381-8914-6eea36967d01	c6dd6bbd-c488-4b91-b381-d909ab836795	\N	null	2025-10-20 17:26:11.517053+03
b5bddbf5-c2ee-4990-a237-394b6a5dd226	7619423d-cb07-4381-8914-6eea36967d01	292f04a8-5cf8-44b8-bc40-36c68437dfd9	\N	\N	2025-10-20 17:26:13.427538+03
\.


--
-- TOC entry 5080 (class 0 OID 16670)
-- Dependencies: 233
-- Data for Name: attempts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attempts (id, exam_id, user_id, status, score_percent, started_at, submitted_at, due_at) FROM stdin;
863af9e0-b0bb-428e-b507-e3faba85abca	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 05:16:18.690896+03	2025-10-20 02:18:16.682941+03	2025-10-20 07:16:18.690896+03
82da63f3-e163-41ba-b6ab-d080cbc30fc6	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 05:22:37.866378+03	2025-10-20 02:22:48.410622+03	2025-10-20 07:22:37.866378+03
85bdf016-c9a7-4ef5-8598-b6dbef9b627b	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 05:27:45.291574+03	2025-10-20 02:47:31.258131+03	2025-10-20 07:27:45.291574+03
5fd6898a-826a-4598-9a1d-02e27bab7bd4	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 05:47:40.840345+03	2025-10-20 02:47:47.604643+03	2025-10-20 07:47:40.840345+03
0d8b7fed-f5ee-4fee-ad7d-b97724c68a43	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 16:21:19.74912+03	2025-10-20 13:21:24.789336+03	2025-10-20 18:21:19.74912+03
01dcb31d-7198-47ee-85f5-60e295efb9a7	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 16:22:32.176801+03	2025-10-20 13:22:35.486825+03	2025-10-20 18:22:32.176801+03
2993a9a7-f9dc-4cac-8714-94e7879a98f7	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 16:23:50.491767+03	2025-10-20 13:23:55.107425+03	2025-10-20 18:23:50.491767+03
9195d614-3654-42d3-b6c4-38360237206c	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 16:24:05.854458+03	2025-10-20 13:24:10.566366+03	2025-10-20 18:24:05.854458+03
96787386-263a-41a0-ac32-3e04ea5fc1ff	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	in_progress	\N	2025-10-20 16:24:47.468707+03	\N	2025-10-20 18:24:47.468707+03
85c23a7b-c67d-4926-8671-93eb18c65542	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:07:14.699486+03	2025-10-20 17:07:29.825039+03	2025-10-20 22:07:14.699486+03
a8db8cfb-a0c4-4c91-944e-a4a97e9430a3	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:08:15.915454+03	2025-10-20 17:08:18.793093+03	2025-10-20 22:08:15.915454+03
df518ada-634a-4d43-82bb-3d3536ba6123	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:10:36.637617+03	2025-10-20 17:10:40.085508+03	2025-10-20 22:10:36.637617+03
43222e87-bbd5-429a-88ca-0b21423f2c51	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:20:08.815432+03	2025-10-20 17:20:12.83695+03	2025-10-20 22:20:08.815432+03
5796b076-78aa-4904-aae7-0eafefd727d0	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:20:35.511571+03	2025-10-20 17:20:44.535811+03	2025-10-20 22:20:35.511571+03
de19e64f-6fb5-4110-875a-a4ce39cd5e08	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:22:22.177446+03	2025-10-20 17:22:31.495411+03	2025-10-20 22:22:22.177446+03
7619423d-cb07-4381-8914-6eea36967d01	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	a6fc1bbb-1f24-41a1-b3c4-3370b3c5fab5	submitted	\N	2025-10-20 20:26:08.631232+03	2025-10-20 17:26:13.437716+03	2025-10-20 22:26:08.631232+03
\.


--
-- TOC entry 5076 (class 0 OID 16541)
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
-- TOC entry 5073 (class 0 OID 16505)
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
-- TOC entry 5075 (class 0 OID 16534)
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
-- TOC entry 5071 (class 0 OID 16463)
-- Dependencies: 224
-- Data for Name: login_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_history (id, user_id, login_timestamp, ip_address) FROM stdin;
\.


--
-- TOC entry 5074 (class 0 OID 16515)
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
-- TOC entry 5066 (class 0 OID 16411)
-- Dependencies: 219
-- Data for Name: majors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.majors (id, name) FROM stdin;
1	Комп'ютерні науки
2	Прикладна математика
3	Інженерія програмного забезпечення
\.


--
-- TOC entry 5084 (class 0 OID 16811)
-- Dependencies: 237
-- Data for Name: matching_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.matching_data (id, question_id, prompt, correct_match) FROM stdin;
\.


--
-- TOC entry 5079 (class 0 OID 16657)
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
-- TOC entry 5078 (class 0 OID 16643)
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
-- TOC entry 5083 (class 0 OID 16723)
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
-- TOC entry 5077 (class 0 OID 16629)
-- Dependencies: 230
-- Data for Name: questions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.questions (id, exam_id, question_type, title, "position", points) FROM stdin;
16e8b1f9-af8f-4b56-9bbd-d65d6a658526	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	single_choice	Чому дорівнює визначник (детермінант) матриці [[a, b], [c, d]]?	1	8
8e45a053-35f9-4c82-a9ad-dfa4fac62137	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	multi_choice	Які з наступних тверджень про вектори є вірними?	2	15
0b6926df-8c4e-413f-a7ee-66cd7b4de6b8	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	short_answer	Знайдіть ранг матриці [[1, 2, 3], [2, 4, 6]]. Введіть відповідь у вигляді числа.	3	15
86eb5e7f-2889-417c-84b7-4833fb7656e7	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	long_answer	Поясніть своїми словами, що таке власні вектори та власні значення матриці.	4	39
b5130cc8-1837-4715-9749-68b879fd5f5d	e5f6a7b8-c9d0-4e1f-2a3b-4c5d6e7f8a9b	matching	Встановіть відповідність між поняттям та його математичним виразом.	5	23
c66488df-9d33-4e77-aab6-320762a544eb	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	single_choice	Яка часова складність алгоритму бінарного пошуку в відсортованому масиві?	1	25
54ae4cd3-f8ba-4997-9369-bcacc6981907	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	multi_choice	Які з наведених структур даних працюють за принципом LIFO (Last-In, First-Out)?	2	25
8ac581ea-4236-456f-b917-c71bfda342fb	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	short_answer	Як називається структура даних, яка зберігає пари "ключ-значення"?	3	25
57d4d112-26c3-4c36-b03a-9c671471193a	a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d	long_answer	Поясніть своїми словами різницю між масивом (Array) та зв'язаним списком (Linked List), вказавши переваги та недоліки кожного.	4	25
b7d35cb0-5ee7-4ca0-b0a9-2719c3192797	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	single_choice	Чому дорівнює похідна функції f(x) = x³?	1	30
b9c9df43-6293-487a-84ef-d925a6d047e3	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	short_answer	Обчисліть границю lim(x->∞) (1/x).	2	30
ba3e241d-aeec-43a4-8086-f2c025d3a35a	b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e	matching	Встановіть відповідність між функцією та її похідною.	3	40
e9c4b680-8443-43e0-b05e-e8a56f61d40d	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	single_choice	Яка команда SQL використовується для вибірки даних з бази даних?	1	25
a599186c-5893-4137-ada0-3aa79fd902ee	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	multi_choice	Які з наведених операторів належать до DDL (Data Definition Language)?	2	40
732eb6fb-2faf-41ee-979f-c7e0aa2d454f	c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f	long_answer	Опишіть, що таке перша нормальна форма (1НФ) в реляційних базах даних.	3	35
c6dd6bbd-c488-4b91-b381-d909ab836795	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	single_choice	Який вид тестування виконується для перевірки того, що нові зміни не зламали існуючий функціонал?	1	30
32ea01f5-33ec-4ff8-891a-b48349f9078a	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	multi_choice	Які з наведених видів тестування належать до нефункціональних?	2	40
292f04a8-5cf8-44b8-bc40-36c68437dfd9	d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a	matching	Встановіть відповідність між рівнем тестування та його описом.	3	30
\.


--
-- TOC entry 5064 (class 0 OID 16400)
-- Dependencies: 217
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id, name) FROM stdin;
1	student
2	teacher
3	supervisor
\.


--
-- TOC entry 5069 (class 0 OID 16447)
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
-- TOC entry 5068 (class 0 OID 16432)
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
-- TOC entry 5067 (class 0 OID 16421)
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
-- TOC entry 5095 (class 0 OID 0)
-- Dependencies: 225
-- Name: courses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_id_seq', 9, true);


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
-- TOC entry 4875 (class 2606 OID 16545)
-- Name: course_exams course_exams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_pkey PRIMARY KEY (course_id, exam_id);


--
-- TOC entry 4867 (class 2606 OID 16514)
-- Name: courses courses_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_code_key UNIQUE (code);


--
-- TOC entry 4869 (class 2606 OID 16512)
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
-- TOC entry 4865 (class 2606 OID 16471)
-- Name: login_history login_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_pkey PRIMARY KEY (id);


--
-- TOC entry 4871 (class 2606 OID 16519)
-- Name: major_courses major_courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_pkey PRIMARY KEY (major_id, course_id);


--
-- TOC entry 4853 (class 2606 OID 16420)
-- Name: majors majors_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_name_key UNIQUE (name);


--
-- TOC entry 4855 (class 2606 OID 16418)
-- Name: majors majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.majors
    ADD CONSTRAINT majors_pkey PRIMARY KEY (id);


--
-- TOC entry 4899 (class 2606 OID 16817)
-- Name: matching_data matching_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_data
    ADD CONSTRAINT matching_data_pkey PRIMARY KEY (id);


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
-- TOC entry 4849 (class 2606 OID 16409)
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- TOC entry 4851 (class 2606 OID 16407)
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
-- TOC entry 4863 (class 2606 OID 16451)
-- Name: user_majors user_majors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_majors
    ADD CONSTRAINT user_majors_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4861 (class 2606 OID 16436)
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- TOC entry 4857 (class 2606 OID 16431)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4859 (class 2606 OID 16429)
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
-- TOC entry 4917 (class 2620 OID 16731)
-- Name: questions questions_count_update_trigger; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_count_update_trigger AFTER INSERT OR DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.update_exam_question_count_trigger();


--
-- TOC entry 4918 (class 2620 OID 16735)
-- Name: questions questions_reorder_after_delete; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_reorder_after_delete AFTER DELETE ON public.questions FOR EACH ROW EXECUTE FUNCTION public.reorder_questions_on_delete();


--
-- TOC entry 4919 (class 2620 OID 16733)
-- Name: questions questions_set_position_before_insert; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER questions_set_position_before_insert BEFORE INSERT ON public.questions FOR EACH ROW EXECUTE FUNCTION public.set_question_position_on_insert();


--
-- TOC entry 4907 (class 2606 OID 16546)
-- Name: course_exams course_exams_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4908 (class 2606 OID 16551)
-- Name: course_exams course_exams_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.course_exams
    ADD CONSTRAINT course_exams_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4912 (class 2606 OID 16677)
-- Name: attempts exam_attempts_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT exam_attempts_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4904 (class 2606 OID 16472)
-- Name: login_history login_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_history
    ADD CONSTRAINT login_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- TOC entry 4905 (class 2606 OID 16525)
-- Name: major_courses major_courses_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- TOC entry 4906 (class 2606 OID 16520)
-- Name: major_courses major_courses_major_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.major_courses
    ADD CONSTRAINT major_courses_major_id_fkey FOREIGN KEY (major_id) REFERENCES public.majors(id) ON DELETE CASCADE;


--
-- TOC entry 4911 (class 2606 OID 16665)
-- Name: matching_pairs matching_pairs_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matching_pairs
    ADD CONSTRAINT matching_pairs_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4910 (class 2606 OID 16652)
-- Name: options options_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.options
    ADD CONSTRAINT options_question_id_fkey FOREIGN KEY (question_id) REFERENCES public.questions(id) ON DELETE CASCADE;


--
-- TOC entry 4909 (class 2606 OID 16638)
-- Name: questions questions_exam_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.questions
    ADD CONSTRAINT questions_exam_id_fkey FOREIGN KEY (exam_id) REFERENCES public.exams(id) ON DELETE CASCADE;


--
-- TOC entry 4915 (class 2606 OID 16712)
-- Name: answer_options student_answer_options_selected_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_selected_option_id_fkey FOREIGN KEY (selected_option_id) REFERENCES public.options(id) ON DELETE CASCADE;


--
-- TOC entry 4916 (class 2606 OID 16707)
-- Name: answer_options student_answer_options_student_answer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answer_options
    ADD CONSTRAINT student_answer_options_student_answer_id_fkey FOREIGN KEY (answer_id) REFERENCES public.answers(id) ON DELETE CASCADE;


--
-- TOC entry 4913 (class 2606 OID 16692)
-- Name: answers student_answers_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.answers
    ADD CONSTRAINT student_answers_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.attempts(id) ON DELETE CASCADE;


--
-- TOC entry 4914 (class 2606 OID 16697)
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


-- Completed on 2025-10-20 20:32:25

--
-- PostgreSQL database dump complete
--

\unrestrict 5fmbcsL1gOKOciiYLbAeZzgQmKFx6FE7ndd9OySb2LCpBaXUPiRnGGHyTbmBSXt

