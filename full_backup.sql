--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Debian 16.8-1.pgdg120+1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: courses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.courses (
    id integer NOT NULL,
    title text NOT NULL,
    description text,
    lesson_count integer NOT NULL,
    created_by bigint NOT NULL,
    approved boolean DEFAULT false,
    number_course integer
);


ALTER TABLE public.courses OWNER TO postgres;

--
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
-- Name: courses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.courses_id_seq OWNED BY public.courses.id;


--
-- Name: lessons; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lessons (
    id integer NOT NULL,
    course_id integer,
    title text NOT NULL,
    video_file_id text,
    homework text,
    extra_material_file text,
    extra_material_link text,
    workbook text
);


ALTER TABLE public.lessons OWNER TO postgres;

--
-- Name: lessons_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lessons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lessons_id_seq OWNER TO postgres;

--
-- Name: lessons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lessons_id_seq OWNED BY public.lessons.id;


--
-- Name: user_lessons; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_lessons (
    id integer NOT NULL,
    user_id bigint NOT NULL,
    lesson_id integer NOT NULL,
    status text DEFAULT 'not_started'::text NOT NULL,
    answer text,
    file_id text,
    submitted_at timestamp without time zone,
    checked_at timestamp without time zone,
    checked_by bigint,
    comment text
);


ALTER TABLE public.user_lessons OWNER TO postgres;

--
-- Name: user_lessons_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_lessons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_lessons_id_seq OWNER TO postgres;

--
-- Name: user_lessons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_lessons_id_seq OWNED BY public.user_lessons.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    fio text NOT NULL,
    username text,
    role text NOT NULL,
    CONSTRAINT users_role_check CHECK ((role = ANY (ARRAY['user'::text, 'admin'::text, 'owner'::text, 'decline'::text])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: courses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses ALTER COLUMN id SET DEFAULT nextval('public.courses_id_seq'::regclass);


--
-- Name: lessons id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lessons ALTER COLUMN id SET DEFAULT nextval('public.lessons_id_seq'::regclass);


--
-- Name: user_lessons id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons ALTER COLUMN id SET DEFAULT nextval('public.user_lessons_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
\.


--
-- Data for Name: courses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.courses (id, title, description, lesson_count, created_by, approved, number_course) FROM stdin;
58	Ислом динининг пайдо бўлиши.\nМуҳаммад шахси	Бу дарсда сиз Ислом динининг қандай пайдо бўлгани ва Муҳаммад шахси ҳақида қисқача билиб оласиз.\nДарсни тинглаш жараёнида иш дафтарини тўлдириб боринг. \nДарсни кўриб бўлгач эса вазифаларни бажаринг ва қўшимча материални ҳам ўрганиб чиқинг.	4	7249141952	t	1
\.


--
-- Data for Name: lessons; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.lessons (id, course_id, title, video_file_id, homework, extra_material_file, extra_material_link, workbook) FROM stdin;
77	58	Масиҳийлик нуқтаи назаридан исломда нажот концепцияси	BAACAgIAAxkBAAPuaEp-q_zmXG4nqObChFbMagwwpvQAAgl2AAK3dTlKFn77dAwjkII2BA	1.Масиҳийлик ва исломдаги нажот тушунчаларининг фарқларини 5 та жиҳатда таққослаб ёзинг.\n2.Гуноҳ, иноят ва қурбонлик тушунчаларини масиҳийлик ва ислом динида қандай изоҳланганини ёзма равишда таққосланг.\n3.Сизнингча, нажот Худо томонидан берилган инъомми ёки инсон амалларига қараб мукофотми? Манбалар билан асосланг.\n4.Исо Масиҳ орқали нажот таълимоти сизда қандай хулосаларга олиб келди? Шахсий фикрингизни ифода этинг.	\N	\N	BQACAgIAAxkBAAPyaEp-tzo-GlSe--PrEnZj4OzUPcYAAq9xAAKt4kFKw1vhIzoxbQY2BA
76	58	Ислом динидаги ахлоқий меъёрлар	BAACAgIAAxkBAAPGaEp2CJNb_hkz8UZyA8fTmkDJlsUAAopwAAKpARBKgq7KfOiMx9g2BA	1.Муҳаммад ва Исонинг ахлоқий қарашларини солиштиринг.\n\n2.Қуръон ва Муқаддас Китобдаги муҳаббат, шафқат ва адолат мавзулари қай тарзда ифода этилганини таҳлил қилинг.\n\n3.Исо ва Муҳаммаднинг душманларига муносабати ҳақидаги оятлар асосида қиёсий таҳлил қилинг.\n\n4.Муҳаммаднинг шогирдларига берган кўрсатмалари ва Исонинг шогирдларига айтган сўзларини таққослаб, уларнинг услубида қандай фарқ борлигини кўрсатинг.\n\n5.Илоҳийлик, гуноҳсизлик ва муҳаббат нуқтаи назаридан Исо ва Муҳаммаднинг шахсини баҳоланг.	\N	https://youtu.be/r0WjXKXInS8?si=UANBVTRMCcjKeM6Z	BQACAgIAAxkBAAPHaEp2FJ_gkIJJich3WFmk_SZWZAIAArZxAAKt4kFKD5u2S5vNkho2BA
74	58	Ислом динининг пайдо бўлиши.\nМуҳаммад шахси	BAACAgIAAxkBAAPCaEp1yP1AuiLHC6xZ6UqNNppq-zIAAmdwAAKpARBK8TtsGl_ktcA2BA	1. Ислом динининг дастлабки тарқалиш жараёнини ижтимоий ва сиёсий жиҳатдан таҳлил қилинг.\n\n2. Хадича ва Варақанинг шахсий жиҳатлари ва уларнинг таъсирини таҳлил қилинг.\n\n3. Муҳаммаднинг турмуш тарзи ва шахсий қарорлари (масалан, хотинлари сони) таълимот мазмунига қандай таъсир қилган?\n\n4. Қуръоннинг 10:94 ва 9:29 оятларини таҳлил қилинг. Уларнинг мазмунидаги фарқлар нима?\n\n5. Муҳаммад қандай пайғамбар экани ҳақида шахсий хулосангизни ёзинг.	\N	https://www.youtube.com/watch?v=h2BrFbjcIVc	BQACAgIAAxkBAAPDaEp14KNUdiLlExf88v2YiisHKi8AAq5xAAKt4kFKs6orFJc4xZg2BA
75	58	Ислом динининг асосий таълимотлари	BAACAgIAAxkBAAPEaEp17j2rNl70i0lT8DgBjsqp-yoAAoJwAAKpARBKnzHsoC_1Yxo2BA	1. Қуръоннинг асосий мавзулари қайсилар? Ҳар бири ҳақида 2-3 жумла ёзинг.\n\n2. Макка ва Мадина сураларининг мазмуний фарқларини солиштиринг.\n\n3. Қуръондаги тил мураккаблиги ва “очиқ-равшан” даъволари ўртасидаги зиддият ҳақида фикрингизни ёзинг.\n\n4. Ҳадисларнинг келиб чиқиши ва уларнинг исломдаги ўрни ҳақида изоҳ беринг.\n\n5. Ислом таълимотларининг бугунги кун мусулмон жамиятида қандай ифода топаётганини таҳлил қилинг.	\N	https://www.youtube.com/watch?v=FN21nlZBqGQ&list=PLkPlbrY3A9lheXXI2lfk1cSH0EICxjf2U&index=2&pp=iAQB	BQACAgIAAxkBAAPFaEp1_URLHLJaJf7Y0_QUhbXAYUcAArBxAAKt4kFKFRxXd2YGOJo2BA
\.


--
-- Data for Name: user_lessons; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_lessons (id, user_id, lesson_id, status, answer, file_id, submitted_at, checked_at, checked_by, comment) FROM stdin;
51	6774411424	74	approved	lesson 1 done	\N	2025-06-12 07:41:30.774684	2025-06-12 07:41:40.59502	\N	\N
53	6774411424	75	approved	lesson 2 done	\N	2025-06-12 07:41:55.451639	2025-06-12 07:42:08.581506	\N	\N
55	6774411424	76	approved	lesson 3 done	\N	2025-06-12 07:42:21.564037	2025-06-12 07:42:27.563035	\N	\N
57	6774411424	77	approved	lesson 4 done	\N	2025-06-12 07:42:48.092602	2025-06-12 07:42:52.864826	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, fio, username, role) FROM stdin;
44319692	Мирзаев Диёр	Dier_mrz	admin
200916374	Mahliyo sayd	MBX1177	user
1662231535	Кувашева Умида	Umida	owner
7249141952	Без ФИО	\N	admin
371259595	Без ФИО		user
5339945035	Umid	umidtv_chat	user
741340595	Без ФИО		user
6774411424	deir	dier_mrzv	user
\.


--
-- Name: courses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.courses_id_seq', 58, true);


--
-- Name: lessons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.lessons_id_seq', 77, true);


--
-- Name: user_lessons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_lessons_id_seq', 58, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: courses courses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.courses
    ADD CONSTRAINT courses_pkey PRIMARY KEY (id);


--
-- Name: lessons lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lessons
    ADD CONSTRAINT lessons_pkey PRIMARY KEY (id);


--
-- Name: user_lessons user_lesson_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons
    ADD CONSTRAINT user_lesson_unique UNIQUE (user_id, lesson_id);


--
-- Name: user_lessons user_lessons_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons
    ADD CONSTRAINT user_lessons_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: lessons lessons_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lessons
    ADD CONSTRAINT lessons_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.courses(id) ON DELETE CASCADE;


--
-- Name: user_lessons user_lessons_checked_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons
    ADD CONSTRAINT user_lessons_checked_by_fkey FOREIGN KEY (checked_by) REFERENCES public.users(id);


--
-- Name: user_lessons user_lessons_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons
    ADD CONSTRAINT user_lessons_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lessons(id);


--
-- Name: user_lessons user_lessons_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_lessons
    ADD CONSTRAINT user_lessons_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

