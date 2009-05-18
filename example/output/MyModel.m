//
//  MyModel.m
//  example

#import "MyModel.h"


@implementation MyModel
@synthesize someItems, text, count;




-(id) initWithSomeitems: (NSArray*) inSomeitems text: (NSString*) inText count: (int) inCount {
    
    if (self = [super init]) {
             self.someItems = inSomeitems;
             self.text = inText;
             self.count = inCount;

    }
    
    return self;
}
    
@end
