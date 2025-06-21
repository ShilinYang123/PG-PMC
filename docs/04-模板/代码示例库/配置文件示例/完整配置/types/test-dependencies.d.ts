/**
 * 测试依赖类型声明文件
 * 3AI工作室 - 为常用测试库提供类型支持
 */

// Supertest 类型声明
declare module 'supertest' {
  import { Server } from 'http';
  
  // Express 类型声明（避免循环依赖）
  interface Express {
    [key: string]: any;
  }

  interface Response {
    status: number;
    text: string;
    body: any;
    header: { [key: string]: string };
    headers: { [key: string]: string };
    type: string;
    charset: string;
    links: object;
    get(field: string): string;
  }

  interface Request {
    attach(field: string, file: string | Buffer, filename?: string): this;
    field(name: string, val: string | number | boolean): this;
    set(field: string, val: string): this;
    set(field: object): this;
    send(data?: any): this;
    query(val: object | string): this;
    type(val: string): this;
    accept(val: string): this;
    auth(user: string, pass: string, options?: { type: 'basic' | 'bearer' }): this;
    withCredentials(): this;
    expect(status: number): this;
    expect(status: number, callback: (err: any, res: Response) => void): this;
    expect(body: any): this;
    expect(body: any, callback: (err: any, res: Response) => void): this;
    expect(field: string, val: string | RegExp): this;
    expect(field: string, val: string | RegExp, callback: (err: any, res: Response) => void): this;
    expect(checker: (res: Response) => any): this;
    expect(checker: (res: Response) => any, callback: (err: any, res: Response) => void): this;
    end(callback?: (err: any, res: Response) => void): this;
    then(resolve?: (res: Response) => void, reject?: (err: any) => void): Promise<Response>;
    catch(reject?: (err: any) => void): Promise<Response>;
  }

  interface SuperTest<T> {
    get(url: string): T;
    post(url: string): T;
    put(url: string): T;
    patch(url: string): T;
    delete(url: string): T;
    del(url: string): T;
    head(url: string): T;
    options(url: string): T;
  }

  function request(app: Express | Server | string): SuperTest<Request>;
  export = request;
}

// MongoDB Memory Server 类型声明
declare module 'mongodb-memory-server' {
  export interface MongoMemoryServerOpts {
    instance?: {
      port?: number;
      ip?: string;
      dbName?: string;
      dbPath?: string;
      storageEngine?: string;
      replSet?: string;
      auth?: boolean;
      args?: string[];
    };
    binary?: {
      version?: string;
      downloadDir?: string;
      platform?: string;
      arch?: string;
      checkMD5?: boolean;
      systemBinary?: string;
    };
    debug?: boolean;
    autoStart?: boolean;
  }

  export class MongoMemoryServer {
    constructor(opts?: MongoMemoryServerOpts);
    static create(opts?: MongoMemoryServerOpts): Promise<MongoMemoryServer>;
    start(): Promise<void>;
    stop(): Promise<boolean>;
    getUri(otherDbName?: string, otherDbOptions?: string): string;
    getConnectionString(otherDbName?: string, otherDbOptions?: string): string;
    getDbName(): string;
    getDbPath(): string;
    getPort(): number;
    getInstanceInfo(): any;
  }

  export class MongoMemoryReplSet {
    constructor(opts?: any);
    static create(opts?: any): Promise<MongoMemoryReplSet>;
    start(): Promise<void>;
    stop(): Promise<boolean>;
    getUri(otherDbName?: string): string;
    getConnectionString(otherDbName?: string): string;
  }
}

// Mongoose 扩展类型声明
declare module 'mongoose' {
  export interface Document {
    _id?: any;
    id?: string;
    __v?: number;
    isNew: boolean;
    $isDefault(): boolean;
    $isDeleted(): boolean;
    isDirectModified(path: string): boolean;
    isDirectSelected(path: string): boolean;
    isInit(path: string): boolean;
    isModified(path?: string): boolean;
    isSelected(path: string): boolean;
    markModified(path: string): void;
    modifiedPaths(): string[];
    save(): Promise<this>;
    toJSON(): any;
    toObject(): any;
    toString(): string;
    validate(): Promise<void>;
    validateSync(): any;
  }

  export interface Model<T extends Document> {
    new (doc?: any): T;
    aggregate(pipeline?: any[]): any;
    bulkWrite(writes: any[]): Promise<any>;
    count(filter?: any): Promise<number>;
    countDocuments(filter?: any): Promise<number>;
    create(doc: any): Promise<T>;
    create(docs: any[]): Promise<T[]>;
    deleteMany(filter?: any): Promise<any>;
    deleteOne(filter?: any): Promise<any>;
    distinct(field: string, filter?: any): Promise<any[]>;
    estimatedDocumentCount(): Promise<number>;
    exists(filter: any): Promise<any>;
    find(filter?: any, projection?: any): any;
    findById(id: any, projection?: any): any;
    findByIdAndDelete(id: any): Promise<T | null>;
    findByIdAndRemove(id: any): Promise<T | null>;
    findByIdAndUpdate(id: any, update: any, options?: any): Promise<T | null>;
    findOne(filter?: any, projection?: any): any;
    findOneAndDelete(filter?: any, options?: any): Promise<T | null>;
    findOneAndRemove(filter?: any, options?: any): Promise<T | null>;
    findOneAndUpdate(filter?: any, update?: any, options?: any): Promise<T | null>;
    insertMany(docs: any[], options?: any): Promise<T[]>;
    replaceOne(filter?: any, replacement?: any, options?: any): Promise<any>;
    updateMany(filter?: any, update?: any, options?: any): Promise<any>;
    updateOne(filter?: any, update?: any, options?: any): Promise<any>;
  }

  export interface Connection {
    readyState: number;
    db: any;
    host: string;
    port: number;
    name: string;
    close(): Promise<void>;
    dropDatabase(): Promise<void>;
  }

  export function connect(uri: string, options?: any): Promise<Connection>;
  export function disconnect(): Promise<void>;
  export const connection: Connection;
  export class Model<T extends Document> {}
  export class Schema {}
}

// Express 扩展类型声明
declare module 'express' {
  export interface Request {
    body: any;
    params: { [key: string]: string };
    query: { [key: string]: any };
    headers: { [key: string]: string };
    cookies: { [key: string]: string };
    user?: any;
    session?: any;
    ip: string;
    method: string;
    originalUrl: string;
    path: string;
    protocol: string;
    secure: boolean;
    xhr: boolean;
    get(field: string): string | undefined;
  }

  export interface Response {
    status(code: number): this;
    json(obj: any): this;
    send(body?: any): this;
    cookie(name: string, value: string, options?: any): this;
    clearCookie(name: string, options?: any): this;
    redirect(url: string): void;
    redirect(status: number, url: string): void;
    render(view: string, locals?: any, callback?: (err: Error, html: string) => void): void;
    locals: any;
  }

  export interface NextFunction {
    (err?: any): void;
  }

  export interface Express {
    listen(port: number, callback?: () => void): any;
    use(...handlers: any[]): this;
    get(path: string, ...handlers: any[]): this;
    post(path: string, ...handlers: any[]): this;
    put(path: string, ...handlers: any[]): this;
    delete(path: string, ...handlers: any[]): this;
    patch(path: string, ...handlers: any[]): this;
  }

  function express(): Express;
  export = express;
}

export {};