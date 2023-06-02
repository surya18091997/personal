import requests,time
import pandas as pd,psycopg2



class Get_and_download_products_file:
    #getting input file location/url
    def __init__(self):
        self.file = None
    def get_file(self): 
            file_url=input ("Please provide compressed products file path:     ")
            self.file=pd.read_csv(file_url, compression='gzip', sep=',')



class Process_file:

    def __init__(self,file,db_name):
        self.conn=None
        self.file=file
        self.db_name=db_name
    
    def enable_connection(self):
        self.conn = psycopg2.connect(
    host="localhost",
    database=self.db_name,
    user="postgres",
    password="1897")


    def new_process(self):
        cursor = self.conn.cursor()
        cursor.execute("""create table if not exists products(
                        name varchar,
                        sku varchar PRIMARY KEY,
                        description varchar
                        )""")
        self.conn.commit()               
        dic=self.file.to_dict('records')
        cursor.executemany("INSERT INTO "+self.db_name+""" (name,sku,description) VALUES (%(name)s, %(sku)s, %(description)s) ON CONFLICT (sku) DO UPDATE SET name = %(name)s ,description = %(description)s;""",dic)
        self.conn.commit()
        print("Database import is finished")

    def agg_query(self):
        cursor = self.conn.cursor()
        cursor.execute("""DROP TABLE IF EXISTS agg_products""")
        self.conn.commit()
        cursor.execute("""create table agg_products as (select name,count(*) as no_of_products from """+self.db_name+"""
                            group by name)""")
        self.conn.commit()
        print("Aggregate table is generated")


       


       

        

def main():
    new=Get_and_download_products_file()
    new.get_file()
    process=Process_file(new.file,"products")
    process.enable_connection()
    process.new_process()
    process.agg_query()

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
