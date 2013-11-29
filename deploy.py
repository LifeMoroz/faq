import MySQLdb as db

if __name__ == '__main__':
    print 'Deploying project'
    con = db.connect(user="root", passwd="local")
    cur = con.cursor()
    print 'Creating database'
    cur.execute('CREATE DATABASE faq_test;')
