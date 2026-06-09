# Завдання: реалізувати фічу «ручне введення призначень» цілком. Репо bptracker-frontend. 

Vue 3 
Контракт бекенду (готовий, не чіпати):

GET /schemas → TreatmentSchema[] (auth)
POST /schemas body { doctor: string, prescribedOn?: string (YYYY-MM-DD), schedule, setActive: boolean } (auth)
PUT /schemas/{id} body { doctor, prescribedOn?, schedule } (auth)
POST /schemas/{id}/activate (auth)
GET /schemas/active — без змін
schedule = { Morning?: Med[], Day?: Med[], Evening?: Med[] }, Med = { Medicine: string, Amount: string, Condition: string }. Amount завжди рядок ("0.5","1","2"). Порожня Condition → шли "None". Ключі бекенд приймає case-insensitive, але шли одразу PascalCase.
У відповідях schedule приходить у полі scheduleDocument; на запис шли поле schedule.
Id генерує бекенд — у формі не показувати й не слати.

Зробити:

src/types/api.ts — розширити:

ts   export interface MedicationEntry { Medicine: string; Amount: string; Condition: string; }
   export interface TreatmentSchema {
     id: string;
     doctor: string | null;
     prescribedOn: string | null;   // YYYY-MM-DD
     createdAt: string;
     isActive: boolean;
     scheduleDocument: Record<string, MedicationEntry[]> | null;
   }
   export interface SchemaScheduleDto { Morning?: MedicationEntry[]; Day?: MedicationEntry[]; Evening?: MedicationEntry[]; }
   export interface CreateSchemaDto { doctor: string; prescribedOn?: string; schedule: SchemaScheduleDto; setActive: boolean; }
   export interface UpdateSchemaDto { doctor: string; prescribedOn?: string; schedule: SchemaScheduleDto; }

src/composables/useApi.ts — додати методи за наявним патерном (_fetch, ApiError, httpStatusToCode, credentials:'include'):

getSchemas(signal?): Promise<TreatmentSchema[]> → GET /schemas
createSchema(data: CreateSchemaDto): Promise<TreatmentSchema> → POST /schemas
updateSchema(id, data: UpdateSchemaDto): Promise<TreatmentSchema> → PUT /schemas/{id}
activateSchema(id): Promise<void> → POST /schemas/{id}/activate
Експортувати всі у return.


src/components/SchemaCard.vue — додати підтримку Day, нічого не видаляючи:

TIME_KEYS: додати Day: 'schema.day'.
order: ['Morning', 'Day', 'Afternoon', 'Evening', 'Night'].


stores/schemas.ts — новий Pinia store за патерном measurements.ts (defineStore через setup-функцію):

state: items: ref<TreatmentSchema[]>, loading, error.
getters: active = computed(() => items.value.find(s => s.isActive) ?? null).
actions: fetchSchemas(signal?); create(dto) (після успіху — await fetchSchemas()); update(id, dto) (так само refetch); activate(id) (оптимістично перемкнути isActive локально → виклик API → refetch для звірки). Обробка помилок як у measurements (toMessage, toast).


src/components/SchemaForm.vue — форма створення/редагування (приймає опційний проп schema?: TreatmentSchema для режиму редагування, emit('saved') / emit('cancel')):

3 секції: Ранок/День/Вечір (schema.morning/day/evening в i18n), мапляться на ключі Morning/Day/Evening.
У кожній секції — динамічний список рядків { Medicine, Amount, Condition }: кнопки «+ рядок» / видалити рядок.
Medicine — <input type="text">.
Amount — <select> з опціями 0.5 / 1 / 2 + опція «Інше» → показати <input> для ручного значення. Зберігати завжди як рядок.
Condition — <input type="text">, плейсхолдер «необов'язково». Порожнє → при збірці DTO підставити "None".
doctor — <input list="doctors"> + <datalist id="doctors"> з унікальних doctor наявних схем (взяти зі store).
prescribedOn — <input type="date">, дефолт = сьогодні (локальна дата YYYY-MM-DD).
setActive — <input type="checkbox"> (лише в режимі створення; дефолт — true, якщо схем ще нема).
Id не показувати.
Збірка schedule: включати лише непорожні секції; рядок валідний, якщо Medicine непорожній; Amount обрізати; порожня Condition → "None".
При сабміті — schemaStore.create(dto) або .update(id, dto), тоді emit('saved').
Стиль — нативний CSS у <style scoped>, узгоджений з рештою компонентів дашборда.


src/components/SchemaList.vue — список усіх схем: кожен елемент показує doctor, prescribedOn, badge «активна» для isActive, кнопки «Редагувати» (emit('edit', schema)) і «Зробити активною» (schemaStore.activate(id), схована для активної). Проп schemas: TreatmentSchema[].
src/pages/DashboardPage.vue — таб «Ліки» (currentTab === 2):

Підключити useSchemaStore, у onMounted (для цього табу) — fetchSchemas().
Кнопка «+ Призначення» вгорі → відкриває SchemaForm (модалка або інлайн-секція, узгоджено з наявним патерном діалогів; ConfirmDialog є — глянь, як монтуються оверлеї).
<SchemaList :schemas="schemaStore.items" @edit="..." />.
SchemaCard лишити для активної схеми (schemaStore.active) — або прибрати локальний getActiveSchema ref, якщо тепер активну дає store. Звести до одного джерела правди (store).


i18n — додати ключі: schema.day, заголовки форми, лейбли Ранок/День/Вечір, «+ Призначення», «+ рядок», «Інше», «Зробити активною», «Редагувати», «активна», плейсхолдери. Додати в усі наявні локалі-файли.

Критерії приймання:

npm run build і npm run test:run — зелені; tsc без помилок (strict).
Створення схеми з рядками в усіх трьох періодах → одразу видно в SchemaList, активна — у SchemaCard з коректними лейблами Ранок/День/Вечір у правильному порядку.
Amount у payload — рядки; порожня Condition їде як "None"; Id ніде не світиться.
Активна завжди рівно одна після activate (звірка через refetch).
credentials:'include' на всіх нових запитах.

Не чіпати: фото-флоу, measurements, auth, бекенд.